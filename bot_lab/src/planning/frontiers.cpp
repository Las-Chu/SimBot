#include <planning/frontiers.hpp>
#include <planning/motion_planner.hpp>
#include <common/grid_utils.hpp>
#include <slam/occupancy_grid.hpp>
#include <lcmtypes/robot_path_t.hpp>
#include <queue>
#include <set>
#include <cassert>


bool is_frontier_cell(int x, int y, const OccupancyGrid& map);
frontier_t grow_frontier(Point<int> cell, const OccupancyGrid& map, std::set<Point<int>>& visitedFrontiers);
robot_path_t path_to_frontier(const frontier_t& frontier, 
                              const pose_xyt_t& pose, 
                              const OccupancyGrid& map,
                              const MotionPlanner& planner);
pose_xyt_t nearest_navigable_cell(pose_xyt_t pose, 
                                  Point<float> desiredPosition, 
                                  const OccupancyGrid& map,
                                  const MotionPlanner& planner);
pose_xyt_t search_to_nearest_free_space(Point<float> position, const OccupancyGrid& map, const MotionPlanner& planner);
double path_length(const robot_path_t& path);


std::vector<frontier_t> find_map_frontiers(const OccupancyGrid& map, 
                                           const pose_xyt_t& robotPose,
                                           double minFrontierLength)
{
    /*
    * To find frontiers, we use a connected components search in the occupancy grid. Each connected components consists
    * only of cells where is_frontier_cell returns true. We scan the grid until an unvisited frontier cell is
    * encountered, then we grow that frontier until all connected cells are found. We then continue scanning through the
    * grid. This algorithm can also perform very fast blob detection if you change is_frontier_cell to some other check
    * based on pixel color or another condition amongst pixels.
    */
    std::vector<frontier_t> frontiers;
    std::set<Point<int>> visitedCells;
    
    Point<int> robotCell = global_position_to_grid_cell(Point<float>(robotPose.x, robotPose.y), map);
    std::queue<Point<int>> cellQueue;
    cellQueue.push(robotCell);
    visitedCells.insert(robotCell);
  
    // Use a 4-way connected check for expanding through free space.
    const int kNumNeighbors = 4;
    const int xDeltas[] = { -1, 1, 0, 0 };
    const int yDeltas[] = { 0, 0, 1, -1 };
    
    // Do a simple BFS to find all connected free space cells and thus avoid unreachable frontiers
    while(!cellQueue.empty())
    {
        Point<int> nextCell = cellQueue.front();
        cellQueue.pop();
        
        // Check each neighbor to see if it is also a frontier
        for(int n = 0; n < kNumNeighbors; ++n)
        {
            Point<int> neighbor(nextCell.x + xDeltas[n], nextCell.y + yDeltas[n]);
            
            // If the cell has been visited or isn't in the map, then skip it
            if(visitedCells.find(neighbor) != visitedCells.end() || !map.isCellInGrid(neighbor.x, neighbor.y))
            {
                continue;
            }
            // If it is a frontier cell, then grow that frontier
            else if(is_frontier_cell(neighbor.x, neighbor.y, map))
            {
                frontier_t f = grow_frontier(neighbor, map, visitedCells);
                
                // If the frontier is large enough, then add it to the collection of map frontiers
                if(f.cells.size() * map.metersPerCell() >= minFrontierLength)
                {
                    frontiers.push_back(f);
                }
            }
            // If it is a free space cell, then keep growing the frontiers
            else if(map(neighbor.x, neighbor.y) < 0)
            {
                visitedCells.insert(neighbor);
                cellQueue.push(neighbor);
            }
        }
    }
    
    return frontiers;
}

pose_xyt_t centroid(std::vector<Point<float>> frontier, const pose_xyt_t& robotPose){
    float sum_x = 0.0;
    float sum_y = 0.0;
    for (auto &&i : frontier){
        sum_x += i.x;
        sum_y += i.y;
    }
    pose_xyt_t centroid;
    centroid.theta = robotPose.theta;
    centroid.utime = robotPose.utime;

    centroid.x = sum_x / frontier.size();
    centroid.y = sum_y / frontier.size();
    return centroid;
}

// std::vector<pose_xyt_t&> expand_centroid(pose_xyt_t centroid, float radius){
//     const float xDeltas[8] = {1, -1, 0, 0, 1, -1, 1, -1};
//     const float yDeltas[8] = {0, 0, 1, -1, 1, -1, -1, 1};

//     std::vector<pose_xyt_t&> children;
//     for (int n = 0; n < 8; ++n)
//     {
//         float cell_x = centroid.x + radius * xDeltas[n];
//         float cell_y = centroid.y + radius * yDeltas[n];
//         pose_xyt_t expanded;
//         // Check that the child is inside the map
//         expanded.x = cell_x;
//         expanded.y = cell_y;
//         expanded.utime = centroid.utime;
//         expanded.theta = centroid.theta;
//         children.push_back(expanded);
//     }
//     return children;

// }


robot_path_t plan_path_to_frontier(const std::vector<frontier_t>& frontiers, 
                                   const pose_xyt_t& robotPose,
                                   const OccupancyGrid& map,
                                   const MotionPlanner& planner)
{
    ///////////// TODO: Implement your strategy to select the next frontier to explore here //////////////////
    /*
    * NOTES:
    *   - If there's multiple frontiers, you'll need to decide which to drive to.
    *   - A frontier is a collection of cells, you'll need to decide which one to attempt to drive to.
    *   - The cells along the frontier might not be in the configuration space of the robot, so you won't necessarily
    *       be able to drive straight to a frontier cell, but will need to drive somewhere close.
    */

    

    // pose_xyt_t proposed;
    // proposed.x = 0.99;
    // proposed.y = -0.06;        
    // proposed.x = alpha* proposed.x + (1-alpha) * robotPose.x;
    // proposed.y = alpha* proposed.y + (1-alpha) * robotPose.y;
    // proposed.theta= robotPose.theta;
    // proposed.utime= robotPose.utime;
    // auto planner_orig = planner.getOrigin();
    // auto map_orig = map.get
    // std::printf("planner: %f, %f; map: %f, %f");

    // std::printf("PLANNING PATH FROM ROBOT: %f, %f, TO %f, %f", robotPose.x, robotPose.y, proposed.x, proposed.y);

    // robot_path_t proposedPath = planner.planPath(robotPose, proposed);
    // if (proposedPath.path_length > 1){
    //     std::printf("FOUND PATH of length %d", proposedPath.path_length);
    //     return proposedPath;
    // }

    float alpha = 0.9;

    std::printf("num of frontiers: %d\n", frontiers.size());

    for (auto f: frontiers){
        pose_xyt_t centr = centroid(f.cells, robotPose);
        // check if centroid works
        robot_path_t proposedPath = planner.planPath(robotPose, centr);
        if (proposedPath.path_length > 1){
            std::printf("FOUND PATH of length %d\n", proposedPath.path_length);
            return proposedPath;
        }
        float radius = 0.05;

        while (radius < 1){
            // std::vector<pose_xyt_t&> expanded = expand_centroid(centr, radius);
            const float xDeltas[8] = {1, -1, 0, 0, 1, -1, 1, -1};
            const float yDeltas[8] = {0, 0, 1, -1, 1, -1, -1, 1};

            std::vector<pose_xyt_t> children;
            for (int n = 0; n < 8; ++n)
            {
                float cell_x = centr.x + radius * xDeltas[n];
                float cell_y = centr.y + radius * yDeltas[n];
                pose_xyt_t expanded;
                // Check that the child is inside the map
                expanded.x = cell_x;
                expanded.y = cell_y;
                expanded.utime = centr.utime;
                expanded.theta = centr.theta;
                children.push_back(expanded);
            }
            for (auto c: children){
                robot_path_t proposedPath = planner.planPath(robotPose, c);
                if (proposedPath.path_length > 1){
                    std::printf("FOUND PATH of length %d\n", proposedPath.path_length);
                    return proposedPath;
                }
                
            }
            radius += 0.05;
        }
        
        
    }

    std::printf("no valid frontiers found!\n");

    robot_path_t emptyPath;
    return emptyPath;
    
    return emptyPath;
}


bool is_frontier_cell(int x, int y, const OccupancyGrid& map)
{
    // A cell if a frontier if it has log-odds 0 and a neighbor has log-odds < 0
    // return true; // temp
    
    // A cell must be in the grid and must have log-odds 0 to even be considered as a frontier
    if(!map.isCellInGrid(x, y) || (map(x, y) != 0))
    {
        return false;
    }
    
    const int kNumNeighbors = 4;
    const int xDeltas[] = { -1, 1, 0, 0 };
    const int yDeltas[] = { 0, 0, 1, -1 };

    for(int n = 0; n < kNumNeighbors; ++n)
    {
        // If any of the neighbors are free, then it's a frontier
        // Note that logOdds returns 0 for out-of-map cells, so no explicit check is needed.
        if(map.logOdds(x + xDeltas[n], y + yDeltas[n]) < 0)
        {
            return true;
        }
    }
    
    return false;
}


frontier_t grow_frontier(Point<int> cell, const OccupancyGrid& map, std::set<Point<int>>& visitedFrontiers)
{
    // Every cell in cellQueue is assumed to be in visitedFrontiers as well
    std::queue<Point<int>> cellQueue;
    cellQueue.push(cell);
    visitedFrontiers.insert(cell);
    
    // Use an 8-way connected search for growing a frontier
    const int kNumNeighbors = 8;
    const int xDeltas[] = { -1, -1, -1, 1, 1, 1, 0, 0 };
    const int yDeltas[] = {  0,  1, -1, 0, 1,-1, 1,-1 };
 
    frontier_t frontier;
    
    // Do a simple BFS to find all connected frontier cells to the starting cell
    while(!cellQueue.empty())
    {
        Point<int> nextCell = cellQueue.front();
        cellQueue.pop();
        
        // The frontier stores the global coordinate of the cells, so convert it first
        frontier.cells.push_back(grid_position_to_global_position(nextCell, map));
        
        // Check each neighbor to see if it is also a frontier
        for(int n = 0; n < kNumNeighbors; ++n)
        {
            Point<int> neighbor(nextCell.x + xDeltas[n], nextCell.y + yDeltas[n]);
            if((visitedFrontiers.find(neighbor) == visitedFrontiers.end()) 
                && (is_frontier_cell(neighbor.x, neighbor.y, map)))
            {
                visitedFrontiers.insert(neighbor);
                cellQueue.push(neighbor);
            }
        }
    }
    
    return frontier;
}