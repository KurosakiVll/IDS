from nfstream import NFStreamer
import customPluginocket
import time
import argparse

parser = argparse.ArgumentParser("")
parser.add_argument("networkInterface", type=str, help="network interface name")
parser.add_argument("filter", type=str, help="filter can be either tcp or udp")
args = parser.parse_args()
networkInterface = str(args.networkInterface)
filter = str(args.filter)

my_streamer = NFStreamer(source=networkInterface, # or network interface
                         decode_tunnels=False,
                         bpf_filter=filter, #por exemplo udp 66
                         promiscuous_mode=True, #catpura tudo mesmo que n seja pra aquela interface
                         snapshot_length=1536, #numero (bytes) para capturar de cada pacote
                         idle_timeout=1 , #tempo maximo de inatividade para o flow "expirar"
                         active_timeout=30, #tempo maximo de atividade
                         accounting_mode=0,
                         udps=customPlugin.CustomPlugin(), #none ou podemos implementar um custom
                         n_dissections=0, #numero de pacotes por flow
                         statistical_analysis=True, #calcula medias, variancia etc dos dados
                        )
for flow in my_streamer:
    print(flow, flush=True)
    data_dictionary = {
        "Destination Port": [flow.dst_port],
        "Flow Duration": [flow.udps.flow_duration],
        "Total Fwd Packets": [flow.src2dst_packets],
        "Total Backward Packets": [flow.dst2src_packets],
        "Total Length of Fwd Packets": [flow.udps.totlen_fwd_pkts],
        "Total Length of Bwd Packets": [flow.udps.totlen_bwd_pkts],
        "Fwd Packet Length Max": [flow.src2dst_max_ps],
        "Fwd Packet Length Min": [flow.src2dst_min_ps],
        "Fwd Packet Length Mean": [flow.src2dst_mean_ps],
        "Fwd Packet Length Std": [flow.src2dst_stddev_ps],
        "Bwd Packet Length Max": [flow.dst2src_max_ps],
        "Bwd Packet Length Min": [flow.dst2src_min_ps],
        "Bwd Packet Length Mean": [flow.dst2src_mean_ps],
        "Bwd Packet Length Std": [flow.dst2src_stddev_ps],
        "Flow Bytes/s": [flow.udps.flow_byts_s],
        "Flow Packets/s": [flow.udps.flow_pkts_s],
        "Flow IAT Mean": [flow.bidirectional_mean_piat_ms],
        "Flow IAT Std": [flow.bidirectional_stddev_piat_ms],
        "Flow IAT Max": [flow.bidirectional_max_piat_ms],
        "Flow IAT Min": [flow.bidirectional_min_piat_ms],
        "Fwd IAT Total": [flow.udps.fwd_iat_tot],
        "Fwd IAT Mean": [flow.src2dst_mean_piat_ms],
        "Fwd IAT Std": [flow.src2dst_stddev_piat_ms],
        "Fwd IAT Max": [flow.src2dst_max_piat_ms],
        "Fwd IAT Min": [flow.src2dst_min_piat_ms],
        "Bwd IAT Total": [flow.udps.bwd_iat_tot],
        "Bwd IAT Mean": [flow.dst2src_mean_piat_ms],
        "Bwd IAT Std": [flow.dst2src_stddev_piat_ms],
        "Bwd IAT Max": [flow.dst2src_max_piat_ms],
        "Bwd IAT Min": [flow.dst2src_min_piat_ms],
        "Fwd PSH Flags": [flow.src2dst_psh_packets],
        "Bwd PSH Flags": [flow.dst2src_psh_packets],
        "Fwd URG Flags": [flow.src2dst_urg_packets],
        "Bwd URG Flags": [flow.dst2src_urg_packets],
        "Fwd Header Length": [flow.udps.fwd_header_len],
        "Bwd Header Length": [flow.udps.bwd_header_len],
        "Fwd Packets/s": [flow.udps.fwd_pkts_s],
        "Bwd Packets/s": [flow.udps.bwd_pkts_s],
        "Min Packet Length": [flow.bidirectional_min_ps],
        "Max Packet Length": [flow.bidirectional_max_ps],
        "Packet Length Mean": [flow.bidirectional_mean_ps],
        "Packet Length Std": [flow.bidirectional_stddev_ps],
        "Packet Length Variance": [flow.udps.pkt_len_var],
        "FIN Flag Count": [flow.bidirectional_fin_packets],
        "SYN Flag Count": [flow.bidirectional_syn_packets],
        "RST Flag Count": [flow.bidirectional_rst_packets],
        "PSH Flag Count": [flow.bidirectional_psh_packets],
        "ACK Flag Count": [flow.bidirectional_ack_packets],
        "URG Flag Count": [flow.bidirectional_urg_packets],
        "CWE Flag Count": [flow.src2dst_urg_packets],
        "ECE Flag Count": [flow.bidirectional_ece_packets],
        "Down/Up Ratio": [flow.udps.down_up_ratio],
        "Average Packet Size": [flow.bidirectional_mean_ps],
        "Avg Fwd Segment Size": [flow.src2dst_mean_ps],
        "Avg Bwd Segment Size": [flow.dst2src_mean_ps],
        "Fwd Avg Bytes/Bulk": [flow.udps.fwd_byts_b_avg],
        "Fwd Avg Packets/Bulk": [flow.udps.fwd_pkts_b_avg],
        "Fwd Avg Bulk Rate": [flow.udps.fwd_blk_rate_avg],
        "Bwd Avg Bytes/Bulk": [flow.udps.bwd_byts_b_avg],
        "Bwd Avg Packets/Bulk": [flow.udps.bwd_pkts_b_avg],
        "Bwd Avg Bulk Rate": [flow.udps.bwd_blk_rate_avg],
        "Subflow Fwd Packets": [flow.src2dst_packets],
        "Subflow Fwd Bytes": [flow.udps.totlen_fwd_pkts],
        "Subflow Bwd Packets": [flow.dst2src_packets],
        "Subflow Bwd Bytes": [flow.udps.totlen_bwd_pkts],
        "Init_Win_bytes_forward": [flow.udps.init_fwd_win_byts],
        "Init_Win_bytes_backward": [flow.udps.init_bwd_win_byts],
        "act_data_pkt_fwd": [flow.udps.fwd_act_data_pkts],
        "min_seg_size_forward": [flow.src2dst_min_ps],
        "Active Mean": [flow.udps.active_mean],
        "Active Std": [flow.udps.active_std],
        "Active Max": [flow.udps.active_max],
        "Active Min": [flow.udps.active_min],
        "Idle Mean": [flow.udps.idle_mean],
        "Idle Std": [flow.udps.idle_std],
        "Idle Max": [flow.udps.idle_max],
        "Idle Min": [flow.udps.idle_min]
    }
    newData = customPlugin.pd.DataFrame.from_records(data=data_dictionary)    
    try:
        file = customPlugin.pd.read_csv(customPlugin.CSV_PATH)
        mergedData = customPlugin.pd.merge(file, newData, how="outer")
        print("writing to a csv...")
        mergedData.to_csv(customPlugin.CSV_PATH, index=False)
    except Exception as e:
        print("Exception: " + str(e))
        newData.to_csv(customPlugin.CSV_PATH, index=False)