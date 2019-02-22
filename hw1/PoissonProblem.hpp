/**
 *  @file PoissonProblem.hpp
 *  @brief Class defining one instance of the 1D Poisson problem, i.e. boundary values, f(x), and
 *  the number of grid points.
 * 
 *  @author Michael S. Emanuel
 *  @date 2019-02-20
 */

// *********************************************************************************************************************
#pragma once

// Silence selected GCC warnings
#ifdef __GNUC__
#pragma GCC diagnostic ignored "-Wreorder"
#pragma GCC diagnostic ignored "-Wsign-compare"
#pragma GCC diagnostic ignored "-Wcatch-value="
#endif

// *********************************************************************************************************************
// Libraries
#include <vector>
    using std::vector;

#include <string>
    using std::string;

#include <iostream>
    using std::cout;

#include <boost/format.hpp>
    using boost::format;

// YAML
#include <yaml-cpp/yaml.h>

// *********************************************************************************************************************
/**
 * @class PoissonProblem
 *  @brief Class to define and solve one instance of the 1D Poisson problem.
 */
class PoissonProblem
{
public:
    /** Default constructor: create an empty problem instance     */
    PoissonProblem();

    /** Constructor: load from a YAML file
     * @param[in] fname the name of the YAML configuration file, e.g. my_problem.yml
     */
    PoissonProblem(string fname);

    /// Write a summary to the console
    void summary();

    /** Create the element stiffness matrix, K_element, of size kxk
     * 
     * @param[in] i the element row number, e.g. 1 or 2
     * @param[in] j the element column number, e.g. 1 or 2
     * @param[out] Ke, an array of size k^2
     * 
     * This matrix will be stored in column major order for LAPACK compatibility.
     */
    void K_element(int i, int j, double *Ke);

private:
    /// Vector of sampled values of f(x) at the node points
    vector<double> f;

    /// The boundary condition u(1) = g
    double g;

    /// The boundary condition u_x(0) = h
    double h;

    /// The number of elements, e.g. 1024
    int n;

    /// The degrees of freedom for each node, e.g. 2 for piecewise linear elements
    int k;

    /// Order of Gaussian Quadrature to use, e.g. 1 to use the midpoint
    int q;

    /// The name of the configuration file
    string fname;

};
