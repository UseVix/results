ros2 run rangeini robosense_compressor --ros-args --log-level compressor:=debug > compressor_robosense_elektro_hall.txt 2>&1 &
PID1=$!
ros2 run rangeini robosense_decompressor --ros-args --log-level decompressor:=debug > decompressor_robosense_elektro_hall.txt 2>&1 &
PID2=$!
ros2 bag play /dataset/NTNU_Unified_Autonomy_Stack_Datasets/elektro_hall_packets/ -r 0.5 --remap "/rslidar_packets:=/lidar_packets"
# Kill the actual underlying C++ processes safely
pkill -SIGINT -f "robosense_compressor"
pkill -SIGINT -f "robosense_decompressor"
sleep 2
# Wait a brief moment for graceful shutdown
ros2 run rangeini compressor --ros-args --log-level debug > compressor_hesai_campus_fog.txt 2>&1 &
PID1=$!
ros2 run rangeini decompressor --ros-args --log-level debug > decompressor_hesai_campus_fog.txt 2>&1 &
PID2=$!
ros2 bag play /dataset/NTNU_Unified_Autonomy_Stack_Datasets/campus_fog_packets/ -r 0.5
# Kill the actual underlying C++ processes safely
pkill -SIGINT -f "compressor"
pkill -SIGINT -f "decompressor"
sleep 2
while read -r line
do
    sequence_name=$(basename "$line")
    ros2 run rangeini ouster_compressor --ros-args --log-level debug > compressor_ouster_${sequence_name}.txt 2>&1 &
    PID1=$!
    ros2 run rangeini ouster_decompressor --ros-args --log-level debug > decompressor_ouster_${sequence_name}.txt 2>&1 &
    PID2=$!
    ros2 bag play $line -r 0.5 --remap "/os_node/lidar_packets:=/lidar_packets" --topic /os_node/lidar_packets </dev/null
    # Kill the actual underlying C++ processes safely
    pkill -SIGINT -f "ouster_compressor"
    pkill -SIGINT -f "ouster_decompressor"
    sleep 2
    done < /results/sequence_list.txt

