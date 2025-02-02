#include <common/lcm_config.h>
#include <mbot/mbot_channels.h>
#include <lcmtypes/robot_path_t.hpp>
#include <lcm/lcm-cpp.hpp>
#include <iostream>
#include <unistd.h>
#include <cmath>

int main(int argc, char** argv)
{std::cout << "here" <<std::endl;
    int numTimes = 1;
    
    if(argc > 1)
    {
        numTimes = std::atoi(argv[1]);
    }
    
    std::cout << "Commanding robot to drive around MAZE!! " << numTimes << " times.\n";
    
    robot_path_t path;
    path.path.resize(numTimes * 4);
    
    pose_xyt_t nextPose;
    
    nextPose.x = 0.0f;
    nextPose.y = 0.61f;
    nextPose.theta = M_PI_2;
    for(int n = 0; n < numTimes; ++n)
    {
        path.path[4*n] = nextPose;
    }
    
    nextPose.x = -0.61f;
    nextPose.y = 0.61f;
    nextPose.theta = 0;
    for(int n = 0; n < numTimes; ++n)
    {
        path.path[4*n + 1] = nextPose;
    }
    
    nextPose.x = -0.61f;
    nextPose.y = 1.1f;
    nextPose.theta = -M_PI_2;
    for(int n = 0; n < numTimes; ++n)
    {
        path.path[4*n + 2] = nextPose;
    }
    
    nextPose.x = 0.61f;
    nextPose.y = 1.2f;
    nextPose.theta = 0;
    for(int n = 0; n < numTimes; ++n)
    {
        path.path[4*n + 3] = nextPose;
    }
    
    // Return to original heading after completing all circuits
//    nextPose.theta = 0.0f;
//    path.path.push_back(nextPose);
    
    nextPose.x = 0.0f;
    nextPose.y = 0.0f;
    nextPose.theta = 0.0f;
    path.path.insert(path.path.begin(), nextPose);
    
    path.path_length = path.path.size();
    
    lcm::LCM lcmInstance(MULTICAST_URL);
	std::cout << "publish to: " << CONTROLLER_PATH_CHANNEL << std::endl;
    lcmInstance.publish(CONTROLLER_PATH_CHANNEL, &path);
    sleep(1);

    return 0;
}
