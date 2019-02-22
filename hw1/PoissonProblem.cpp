/**
 *  @file PoissonProblem.cpp
 *  @brief Implementation of PoissonProblem class.
 * 
 *  @author Michael S. Emanuel
 *  @date 2019-02-20
 */

// *********************************************************************************************************************
#include "PoissonProblem.hpp"

// *********************************************************************************************************************
// Default Constructor
PoissonProblem::PoissonProblem() :
    f(vector<double>()), g(0.0), h(0.0), n(0), k(0), q(0), fname("")
{}

// *********************************************************************************************************************
// Constructor - build from an input file
PoissonProblem::PoissonProblem(string fname) :
    f(vector<double>()), g(0.0), h(0.0), n(0), k(0), q(0), fname(fname)
{
    // https://stackoverflow.com/questions/45346605/example-for-yaml-cpp-0-5-3-in-linux

    // Load the YAML configuration file
    YAML::Node config = YAML::LoadFile(fname);

    // Set the members to the configured values
    f = config["f"].as<vector<double>>();
    g = config["g"].as<double>();
    h = config["h"].as<double>();
    n = config["n"].as<int>();
    k = config["k"].as<int>();
    q = config["q"].as<int>();

    // Check that length of f is equal to n+1
    if (f.size() != n+1)
    {
        string msg = (format("Error: length of f %1% is not equal to n+1 = %2%.\n") % f.size() % (n+1)).str();
        throw std::runtime_error(msg);
    }
}

// *********************************************************************************************************************
// Constructor
void PoissonProblem::summary()
{
    // Summarize this problem instance
    cout << format("Loaded 1D Poisson Problem from configuration file %1%.\n") % fname;
    cout << format("g=%1%\n") % g;
    cout << format("h=%1%\n") % h;
    cout << format("n=%1%\n") % n;
    cout << format("k=%1%\n") % k;
    cout << format("q=%1%\n") % q;
    cout << format("f vector of %1% elements:\n") % f.size();
    for (double x : f)
    {
        cout << format("%4.2f,  ") % x;
    }
    cout << "\n";
}

// *********************************************************************************************************************
// Build the element stiffness matrix, of size kxk
void PoissonProblem::K_element(int i, int j, double *Ke)
{
    ;
}