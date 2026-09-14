while read -r line
do
    sequence_name=$(basename "$line")
    sed -i 's/ouster_ros\/msg\//ouster_sensor_msgs\/msg\//g' ${line}/metadata.yaml
    sqlite3 ${line}${sequence_name}_0.db3 "UPDATE topics SET type = 'ouster_sensor_msgs/msg/PacketMsg' WHERE name = '/os_node/lidar_packets';"
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

