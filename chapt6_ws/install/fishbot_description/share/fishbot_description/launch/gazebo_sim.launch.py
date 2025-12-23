import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
import os
import launch_ros.parameter_descriptions
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution
from ros_gz_bridge.actions import RosGzBridge
from launch_ros.actions import Node  # 确保导入 Node


def generate_launch_description():
    # 获取功能包的share路径
    url_package_path = get_package_share_directory('fishbot_description')
    default_bridge_yaml_path = os.path.join(url_package_path,'config','bridge.yaml')
    default_xacro_path = os.path.join(url_package_path, 'urdf', 'fishibot/fishibot.urdf.xacro')
    default_gazebo_world_path = os.path.join(url_package_path, 'world', 'custom_room.world')
    # 声明一个xacro的参数 ros2 launch fisbot_description ... model:=...xrco
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_xacro_path), description='加载模型的文件路径'
    )
    # 通过将xacro转换成urdf格式，并转换成参数值对象，传入robot_state_publisher
    substitutions_command_result = launch.substitutions.Command(['xacro ', launch.substitutions.LaunchConfiguration('model')])
    robot_description_value = launch_ros.parameter_descriptions.ParameterValue(substitutions_command_result, value_type=str)

    # robot_state_pubsher作为发布者发布机器人模型消息
    action_robot_state_publisher = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description_value,
            'use_sim_time': True  # 关键：添加这行
            }]
    )
    
    # action_joint_state_publisher = launch_ros.actions.Node(
    #     package='joint_state_publisher',
    #     executable='joint_state_publisher'
    # )
    # action_rviz_node = launch_ros.actions.Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     arguments=['-d', default_rviz_config_path]
    # )

    # action_launch_gazebo = launch.actions.IncludeLaunchDescription(
    #     launch.launch_description_sources.PythonLaunchDescriptionSource(
    #         [get_package_share_directory('gazebo_ros'),'/launch','gazebo.launch.py']
    #     ),
    #     launch_arguments=[('world', default_gazebo_world_path), ("verbose", 'true')]
    # )

    # action_launch_gazebo = launch.actions.ExecuteProcess(
    # cmd=[
    #     'gz', 'sim',
    #     '-v', '4',                    # 对应 verbose='true'（4级详细日志）
    #     '-r', default_gazebo_world_path,  # 对应 world 参数
    # ],
    # output='screen',                   # 输出到屏幕
    # shell=False                         # 直接执行，不通过shell
    # )
    action_launch_gazebo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [get_package_share_directory('ros_gz_sim'),'/launch','/gz_sim.launch.py']
        ),
       
        launch_arguments={
            'gz_args': f'{default_gazebo_world_path} -v 4 -r',
            'on_exit_shutdown': 'true'  # 重要：当 Gazebo 退出时关闭所有节点
        }.items()
        #launch_arguments=[('world',default_gz_world_path),('verbose','true')]
    )

    action_spawn_entity = launch_ros.actions.Node(
    package='ros_gz_sim',
    executable='create',
    name='spawn_fishbot',
    arguments=[
        '-topic', '/robot_description', # 从该话题获取模型描述
        '-entity', 'fishbot',           # 实体名称
        '-world', 'default',            # 指定要生成到哪个 Gazebo 世界（重要！）
        '-x', '0.0',                    # X 坐标
        '-y', '0.0',                    # Y 坐标
        '-z', '0.2'                     # Z 坐标（放在地面上方一点）
        # 你还可以添加：`-Y`, `-P`, `-R` 来设置偏航、俯仰、滚动角
    ],
    output='screen'
    )

    bridge_name = LaunchConfiguration('bridge_name')
    config_file = LaunchConfiguration('config_file')

    bridge_name = DeclareLaunchArgument(
        'bridge_name',default_value='fishbot_bridge',
        description='Name of ros_gz_bridge node'
    )

    config_file = DeclareLaunchArgument(
        'config_file',default_value=default_bridge_yaml_path,
        description='YAML config file'
    )

    bridge =  RosGzBridge(
       bridge_name=LaunchConfiguration('bridge_name'),
       config_file=LaunchConfiguration('config_file'),
    )


    
    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        action_robot_state_publisher,
        action_launch_gazebo,
        action_spawn_entity,
        bridge_name,
        config_file,
        bridge,
        # lidar_bridge,
        # action_joint_state_publisher,
        # action_rviz_node,
    ])