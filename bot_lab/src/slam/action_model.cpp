#include <lcmtypes/particle_t.hpp>
#include <common/angle_functions.hpp>
#include <cassert>
#include <cmath>
#include <iostream>
#include <slam/action_model.hpp>

using namespace std;

// class ActionModel {
// public:
//     ActionModel(void);

//     // Other member functions and variables...

// private:
//     bool initialized_; // Declare "initialized_" as a nonstatic data member
//     // Other member variables...
// };

ActionModel::ActionModel(void)
: k1_(0.1f) // default: 0.01, 0.00015625f
, k2_(0.005f) // default: 0.005, 0.00007812f
, initialized_(false) // Initialize "initialized_" in the member initializer list
{
    //////////////// TODO: Handle any initialization for your ActionModel /////////////////////////
    std::random_device rd;
    numberGenerator_ = std::mt19937(rd());

}

bool ActionModel::updateAction(const pose_xyt_t& odometry)
{
    ////////////// TODO: Implement code here to compute a new distribution of the motion of the robot ////////////////
    if(!initialized_) {
        previousPose_ = odometry;
        initialized_ = true;
    }

    float deltaX = odometry.x - previousPose_.x;
    float deltaY = odometry.y - previousPose_.y;
    float deltaTheta = angle_diff(odometry.theta, previousPose_.theta);
    float direction = 1.0;

    trans_ = std::sqrt(deltaX * deltaX + deltaY * deltaY);
    rot1_ = angle_diff(std::atan2(deltaY, deltaX), previousPose_.theta); // line 2 in lecture

    if(std::abs(rot1_) > M_PI_2) { // bounding
        rot1_ = angle_diff(M_PI, rot1_);
        direction = -1.0;
    }

    rot2_ = angle_diff(deltaTheta, rot1_); // line 4

    bool moved = (deltaX != 0) || (deltaY != 0) || (deltaTheta != 0);
    if (moved) {
        rot1Std_ = std::sqrt(k1_ * std::abs(rot1_));
        tranStd_ = std::sqrt(k2_ * std::abs(trans_));
        rot2Std_ = std::sqrt(k1_ * std::abs(rot2_));
    }

    utime_ = odometry.utime;
    previousPose_ = odometry;
    trans_ *= direction;

    return moved;
}


particle_t ActionModel::applyAction(const particle_t& sample)
{
    ////////////// TODO: Implement your code for sampling new poses from the distribution computed in updateAction //////////////////////
    // Make sure you create a new valid particle_t. Don't forget to set the new time and new parent_pose.

    particle_t newSample = sample;
    float sampleRot1 = std::normal_distribution<>(rot1_, rot1Std_)(numberGenerator_);
    float sampleRot2 = std::normal_distribution<>(rot2_, rot2Std_)(numberGenerator_);
    float sampleTrans = std::normal_distribution<>(trans_, tranStd_)(numberGenerator_);

    newSample.pose.x += sampleTrans * std::cos(sample.pose.theta + sampleRot1);
    newSample.pose.y += sampleTrans * std::sin(sample.pose.theta + sampleRot1);
    newSample.pose.theta = wrap_to_pi(sample.pose.theta + sampleRot1 + sampleRot2);
    newSample.pose.utime = utime_;
    newSample.parent_pose = sample.pose;

    return newSample;
}