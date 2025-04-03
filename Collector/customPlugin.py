from nfstream import NFPlugin
import pandas as pd
import pickle
import requests
import json
import numpy as np

CSV_PATH = '/shared-data/out.csv'
CLUMP_TIMEOUT = 1
BULK_BOUND = 4
ACTIVE_TIMEOUT = 0.005

class CustomPlugin(NFPlugin):
    def on_init(self, packet, flow):
        super().on_init(packet, flow)
        flow.udps.flow_byts_s = 0
        flow.udps.flow_pkts_s = 0
        flow.udps.flow_duration = 0
        flow.udps.totlen_fwd_pkts = 0
        flow.udps.totlen_bwd_pkts = 0
        flow.udps.fwd_iat_tot = 0
        flow.udps.bwd_iat_tot = 0
        flow.udps.fwd_header_len = 0
        flow.udps.bwd_header_len = 0
        flow.udps.init_fwd_win_byts = 0
        flow.udps.init_bwd_win_byts = 0
        flow.udps.fwd_act_data_pkts = 0
        flow.udps.fwd_pkts_s = 0
        flow.udps.bwd_pkts_s = 0
        flow.udps.pkt_len_var = 0
        flow.udps.down_up_ratio = 0
        
        flow.udps.fwd_byts_b_avg = 0    # Average number of bytes bulk rate with forward direction.
        flow.udps.fwd_pkts_b_avg = 0    # Average number of packets bulk rate with forward direction.
        flow.udps.fwd_blk_rate_avg = 0  # Average number of bulk rate with forward direction.
        flow.udps.bwd_byts_b_avg = 0    # Average number of bytes bulk rate with reverse direction.
        flow.udps.bwd_pkts_b_avg = 0    # Average number of packets bulk rate with reverse direction.
        flow.udps.bwd_blk_rate_avg = 0  # Average number of bulk rate with reverse direction.
        flow.udps.active_mean = 0       # Mean time a flow was active before becoming idle.
        flow.udps.active_std = 0        # Standard deviation time a flow was active before becoming idle.
        flow.udps.active_max = 0        # Maximum time a flow was active before becoming idle.
        flow.udps.active_min = 0        # Minimum time a flow was active before becoming idle.
        flow.udps.idle_mean = 0         # Mean time a flow was idle before becoming active.
        flow.udps.idle_std = 0          # Standard deviation time a idle was active before becoming active.
        flow.udps.idle_max = 0          # Maximum time a flow was idle before becoming active.
        flow.udps.idle_min = 0          # Minimum time a flow was idle before becoming active.
        
        #BULK
        flow.udps.fwd_bulk_start_time = 0
        flow.udps.fwd_bulk_last_time = 0
        flow.udps.fwd_bulk_count = 0
        flow.udps.fwd_bulk_duration = 0
        flow.udps.fwd_bulk_pkt_count = 0
        flow.udps.fwd_bulk_pkt_count_tmp = 0
        flow.udps.fwd_bulk_size = 0
        flow.udps.fwd_bulk_size_tmp = 0
        flow.udps.bwd_bulk_start_time = 0
        flow.udps.bwd_bulk_last_time = 0
        flow.udps.bwd_bulk_count = 0
        flow.udps.bwd_bulk_duration = 0 
        flow.udps.bwd_bulk_pkt_count = 0          
        flow.udps.bwd_bulk_pkt_count_tmp = 0
        flow.udps.bwd_bulk_size = 0
        flow.udps.bwd_bulk_size_tmp = 0



        flow.udps.start_active = 0
        flow.udps.last_active = 0
        flow.udps.active_times = []
        flow.udps.idle_times = []
        
        #first packet in a flow
        #src to dst, fwd
        if packet.direction == 0: 
            flow.udps.totlen_fwd_pkts = packet.raw_size
            flow.udps.fwd_header_len = len(packet.ip_packet)
            flow.udps.init_fwd_win_byts = packet.transport_size
        #dst to src, bwd
        elif packet.direction == 1:
            flow.udps.totlen_bwd_pkts = packet.raw_size
            flow.udps.bwd_header_len = len(packet.ip_packet)
            flow.udps.init_bwd_win_byts = packet.transport_size
        if packet.payload_size > 0:
            flow.udps.fwd_act_data_pkts += 1
        self.bulk_setup(flow, packet)

    def on_update(self, packet, flow):
        super().on_update(packet, flow)
        
        #src to dst, fwd
        if packet.direction == 0:
            flow.udps.totlen_fwd_pkts += packet.raw_size
            flow.udps.fwd_iat_tot += packet.delta_time
            flow.udps.fwd_header_len += len(packet.ip_packet)
            if flow.udps.init_fwd_win_byts == 0:
                flow.udps.init_fwd_win_byts = packet.transport_size
           
        #dst to src, bwd
        elif packet.direction == 1:
            flow.udps.totlen_bwd_pkts += packet.raw_size
            flow.udps.bwd_iat_tot += packet.delta_time
            flow.udps.fwd_header_len += len(packet.ip_packet)
            if flow.udps.init_bwd_win_byts == 0:
                flow.udps.init_bwd_win_byts = packet.transport_size
        if packet.payload_size > 0:
            flow.udps.fwd_act_data_pkts += 1   
        
        self.bulk_setup(flow, packet)

        self.update_active_idle_times(flow, packet)

    def on_expire(self, flow):
        try:
            #calculate extra features:
            duration = flow.bidirectional_duration_ms * 0.001
            flow.udps.flow_duration = duration

            if duration == 0:
                flow.udps.flow_byts_s = 0
                flow.udps.flow_pkts_s = 0
            else:
                flow.udps.flow_byts_s = (flow.bidirectional_bytes / duration)
                flow.udps.flow_pkts_s = (flow.bidirectional_packets / duration)

            flow.udps.fwd_pkts_s = 0 if flow.src2dst_duration_ms == 0 else flow.src2dst_packets / (flow.src2dst_duration_ms * 0.001)
            flow.udps.bwd_pkts_s = 0 if flow.dst2src_duration_ms == 0 else flow.dst2src_packets / (flow.dst2src_duration_ms * 0.001)
            
            #std dev = raiz (variancia)
            #variancia = std dev ^ 2
            flow.udps.pkt_len_var = flow.bidirectional_stddev_ps * flow.bidirectional_stddev_ps
            
            flow.udps.down_up_ratio = flow.dst2src_packets / flow.src2dst_packets if flow.src2dst_packets != 0 else 0

            #bulk features
            if flow.udps.fwd_bulk_count != 0:
                flow.udps.fwd_byts_b_avg = flow.udps.fwd_bulk_size / flow.udps.fwd_bulk_count
                flow.udps.fwd_pkts_b_avg = flow.udps.fwd_bulk_pkt_count / flow.udps.fwd_bulk_count
            if flow.udps.fwd_bulk_duration != 0:
                flow.udps.fwd_blk_rate_avg = flow.udps.fwd_bulk_size / flow.udps.fwd_bulk_duration

            if flow.udps.bwd_bulk_count != 0:
                flow.udps.bwd_byts_b_avg = flow.udps.bwd_bulk_size / flow.udps.bwd_bulk_count
                flow.udps.bwd_pkts_b_avg = flow.udps.bwd_bulk_pkt_count / flow.udps.bwd_bulk_count
            if flow.udps.bwd_bulk_duration != 0:
                flow.udps.bwd_blk_rate_avg = flow.udps.bwd_bulk_size / flow.udps.bwd_bulk_duration

            #active/idle features
            if len(flow.udps.active_times) > 0:
                flow.udps.active_mean = np.mean(flow.udps.active_times)
                flow.udps.active_std = np.sqrt(np.var(flow.udps.active_times))
                flow.udps.active_max = np.max(flow.udps.active_times)
                flow.udps.active_min = np.min(flow.udps.active_times)
            
            if len(flow.udps.idle_times) > 0:
                flow.udps.idle_mean = np.mean(flow.udps.idle_times)
                flow.udps.idle_std = np.sqrt(np.var(flow.udps.idle_times))
                flow.udps.idle_max = np.max(flow.udps.idle_times)
                flow.udps.idle_min = np.min(flow.udps.idle_times)
            
           
        except Exception as e:
            print("Error:", str(e))  
        finally:
            self.cleanup(flow)
    def cleanup(self, flow):
        del flow.udps.fwd_bulk_start_time
        del flow.udps.fwd_bulk_last_time
        del flow.udps.fwd_bulk_count
        del flow.udps.fwd_bulk_duration
        del flow.udps.fwd_bulk_pkt_count
        del flow.udps.fwd_bulk_pkt_count_tmp
        del flow.udps.fwd_bulk_size
        del flow.udps.fwd_bulk_size_tmp
        del flow.udps.bwd_bulk_start_time
        del flow.udps.bwd_bulk_last_time
        del flow.udps.bwd_bulk_count
        del flow.udps.bwd_bulk_duration 
        del flow.udps.bwd_bulk_pkt_count          
        del flow.udps.bwd_bulk_pkt_count_tmp
        del flow.udps.bwd_bulk_size
        del flow.udps.bwd_bulk_size_tmp
        
        del flow.udps.start_active
        del flow.udps.last_active
        del flow.udps.active_times
        del flow.udps.idle_times

    def bulk_setup(self, flow, packet): 
        payload_size = packet.payload_size
        if payload_size == 0:
            return
        
        if packet.direction == 0: #forward
            if flow.udps.bwd_bulk_last_time > flow.udps.fwd_bulk_start_time:
                flow.udps.fwd_bulk_start_time = 0
            if flow.udps.fwd_bulk_start_time == 0: #first packet in bulk
                self.bulk_start(flow, packet)
            else: 
                if (packet.time - flow.udps.fwd_bulk_last_time) > CLUMP_TIMEOUT: 
                    self.bulk_start(flow, packet)
                else: #add to bulk
                    flow.udps.fwd_bulk_pkt_count_tmp += 1
                    flow.udps.fwd_bulk_size_tmp += packet.payload_size
                    if flow.udps.fwd_bulk_pkt_count_tmp == BULK_BOUND: #4 packets
                        flow.udps.fwd_bulk_count += 1
                        flow.udps.fwd_bulk_pkt_count += flow.udps.fwd_bulk_pkt_count_tmp
                        flow.udps.fwd_bulk_size += flow.udps.fwd_bulk_size_tmp
                        flow.udps.fwd_bulk_duration += (packet.time - flow.udps.fwd_bulk_start_time)
                    elif flow.udps.fwd_bulk_pkt_count_tmp > BULK_BOUND: 
                        flow.udps.fwd_bulk_pkt_count += 1
                        flow.udps.fwd_bulk_size += payload_size
                        flow.udps.fwd_bulk_duration += (packet.time - flow.udps.fwd_bulk_last_time)
                    flow.udps.fwd_bulk_last_time = packet.time
        else: #backward
            if flow.udps.fwd_bulk_last_time > flow.udps.bwd_bulk_start_time:
                flow.udps.bwd_bulk_start_time = 0
            if flow.udps.bwd_bulk_start_time == 0: #first packet in bulk
                self.bulk_start(flow, packet)
            else: 
                if (packet.time - flow.udps.bwd_bulk_last_time) > CLUMP_TIMEOUT: 
                    self.bulk_start(flow, packet)
                else: #add to bulk
                    flow.udps.bwd_bulk_pkt_count_tmp += 1
                    flow.udps.bwd_bulk_size_tmp += packet.payload_size
                    if flow.udps.bwd_bulk_pkt_count_tmp == BULK_BOUND: #4 packets
                        flow.udps.bwd_bulk_count += 1
                        flow.udps.bwd_bulk_pkt_count += flow.udps.bwd_bulk_pkt_count_tmp
                        flow.udps.bwd_bulk_size += flow.udps.bwd_bulk_size_tmp
                        flow.udps.bwd_bulk_duration += (packet.time - flow.udps.bwd_bulk_start_time)
                    elif flow.udps.bwd_bulk_pkt_count_tmp > BULK_BOUND: 
                        flow.udps.bwd_bulk_pkt_count += 1
                        flow.udps.bwd_bulk_size += payload_size
                        flow.udps.bwd_bulk_duration += (packet.time - flow.udps.bwd_bulk_last_time)
                    flow.udps.bwd_bulk_last_time = packet.time

    def bulk_start(self, flow, packet):
        #initialize bulk values
        if packet.direction == 0: #fwd
            flow.udps.fwd_bulk_start_time = packet.time
            flow.udps.fwd_bulk_last_time = packet.time
            flow.udps.fwd_bulk_pkt_count_tmp = 1
            flow.udps.fwd_bulk_size_tmp = packet.payload_size
        elif packet.direction == 1: #bwd
            flow.udps.bwd_bulk_start_time = packet.time
            flow.udps.bwd_bulk_last_time = packet.time
            flow.udps.bwd_bulk_pkt_count_tmp = 1
            flow.udps.bwd_bulk_size_tmp = packet.payload_size

    def update_active_idle_times(self, flow, packet):
        #update the values in the lists of active and idle times
        current_time = packet.delta_time

        if (current_time - flow.udps.last_active) > ACTIVE_TIMEOUT:
            duration = abs(float(flow.udps.last_active - flow.udps.start_active))
            if duration > 0:
                flow.udps.active_times.append(1e3 * duration) # 1s = 1000ms
            flow.udps.idle_times.append(1e3 * (current_time - flow.udps.last_active))
            flow.udps.start_active = current_time
            flow.udps.last_active = current_time
        else:
            flow.udps.last_active = current_time