/**
 *  @file PoissonFiniteElement.cpp
 *  @brief Implementation of PoissonFiniteElement class.
 * 
 *  @author Michael S. Emanuel
 *  @date 2019-02-20
 */

// *********************************************************************************************************************
#include "PoissonFiniteElement.hpp"

// *********************************************************************************************************************
// Constructor - build from an input file
// See: https://stackoverflow.com/questions/45346605/example-for-yaml-cpp-0-5-3-in-linux
PoissonFiniteElement::PoissonFiniteElement(string fname) :
    fname(fname), 
    f(vector<double>()), 
    g(0.0), h(0.0), n(0), d(0), q(0),
    x(vector<double>()),
    forceFuncName(""),
    solutionFuncName(""),
    K(nullptr),
    F(nullptr),
    U(nullptr)
{
    try
    {  
        // Load the YAML configuration file
        YAML::Node config = YAML::LoadFile(fname);

        // Set the members to the configured values
        g = config["g"].as<double>();
        h = config["h"].as<double>();
        n = config["n"].as<int>();
        d = config["d"].as<int>();
        q = config["q"].as<int>();

        // Load the force vector by the specified method
        string forceType = config["forceType"].as<string>();
        if (forceType == "VECTOR")
        {
                f = config["f"].as<vector<double>>();
        }
        else if (forceType == "FUNCTION")
        {
            // Initialize force vector to size n+1 with zeros
            f = vector<double>(n+1, 0.0);
            // The name of the force function
            forceFuncName = config["forceFuncName"].as<string>();
            // Look up the force function            
            FuncType forceFunc = FuncByName(forceFuncName);
            // Apply this force function to to the x in the mesh
            for (int i=0; i<=n; ++i)
            {
                double x = double(i) / n;
                f[i] = (*forceFunc)(x);
            }
        }
        else
        {
            string msg = (format("Error: bad force_type %1%; must be VECTOR or FUNCTION.\n") % forceType).str();
            throw std::runtime_error(msg);
        }
              
        // Check that length of f is equal to n+1
        if (f.size() != n+1)
        {
            string msg = (format("Error: length of f %1% is not equal to n+1 = %2%.\n") % f.size() % (n+1)).str();
            throw std::runtime_error(msg);
        }

        // Get the solution function name
        solutionFuncName = config["solutionFuncName"].as<string>();

    }

    // If there was a problem above, e.g. bad file or bad input, will be left an empty PoissonFiniteElement   
    catch (const std::runtime_error &e) 
    {
        cout << e.what();
    }
    catch (...)
    {
        cout << "Unknown exception encountered in PoissonFiniteElement constructor; returning empty problem.";
    }

    // Populate the vector x of node points using a uniform mesh size
    x.resize(n+1);
    for (int i=0; i<=n; ++i)
    {
        x[i] = double(i) / n;
    }
}

// *********************************************************************************************************************
// Destructor
PoissonFiniteElement::~PoissonFiniteElement()
{
    // Don't need to check if they were assigned memory b/c it is safe (and legal) to delete nullptr in C++17
    delete [] K;
    delete [] F;
    delete [] U;
}

// *********************************************************************************************************************
void PoissonFiniteElement::K_element_2(int e, double *Ke)
{
    // Compute the size of this element
    double h = h_e(e);
    // Cache the inverse of h
    double h_inv = 1.0 / h;
    // The result is a symmetric 2x2 matrix; see Hughes p. 45
    // There are 1s on the main diagonal and -1s on the off diagonals
    // Everything is premultiplied by 1 / h

    // The main diagonal of a 2x2 matrix is stored on elements 0 and 3 (first and last)
    Ke[0] = h_inv;
    Ke[3] = h_inv;
    // The off diagonal of a 2x2 matrix is on the other 2 slots
    Ke[1] = -h_inv;
    Ke[2] = -h_inv;
}

// *********************************************************************************************************************
void PoissonFiniteElement::assemble_K()
{
    // Calculation will depend on the degrees of freedom, d
    // For now the only supported configuration is piecewise linear with d=2
    switch (d)
    {
        case 2:
            // Dispatch call to assemble_K_2
            assemble_K_2();
            break;
        default:
            string msg = (format("Error: degrees of frredom d=%i not supported.") % d).str();
            throw std::logic_error(msg);
    }
}

// *********************************************************************************************************************
void PoissonFiniteElement::assemble_K_2()
{
    // TODO: In the future may wish to parallelize this
    // Local storage for K_element(e)
    double Ke[4];

    // Initialize an array for K of size nxn with all zeroes
    K = new double[n*n] {0.0};

    // Iterate over the first n-1 elements, which have the same treatment
    for (int e=0; e<n-1; ++e)
    {
        // Compute K_element for this element
        K_element_2(e, Ke);

        // Increment relevant entries in global K matrix
        // Formula is on bottom of p. 42 in Hughes, equations 1.14.2 through 1.14.5
        // For all Hughes formulas, shift from 1-based to 0-based indexing

        // The two diagonal entries
        // K[e,e] += K_element[1,1]
        K[ij2k(e, e)] += Ke[ij2k_elt(0, 0)];
        // K[e+1, e+1] += K_element[2, 2]
        K[ij2k(e+1, e+1)] += Ke[ij2k_elt(1, 1)];

        // The two off diagonal entries are treated symmetrically
        // K[e,e+1] ++ K_element[1, 2]
        // K[e+1,e] ++ K_element[1, 2]
        K[ij2k(e+1, e)] += Ke[ij2k_elt(1, 0)];
        K[ij2k(e, e+1)] += Ke[ij2k_elt(0, 1)];
    }

    // Handle the last element, e=n-1; only the local node (e,e) contributes
    // because node n is locked by the constraint.
    // See Hughes p. 43, equation 1.14.6.
    int e=n-1;
    K_element_2(e, Ke);
    K[ij2k(e, e)] += Ke[ij2k_elt(0, 0)];
}

// *****************************************************************************************************************
// See Hughes p. 46, top
void PoissonFiniteElement::F_element_2(int e, double *Fe)
{
    // Compute the prefactor C = h_e / 6
    double C = h_e(e) / 6.0;

    // Get the two local forces from f
    double f1 = f[e];
    double f2 = f[e+1];
    
    // Populate Fe using f1 and f2
    Fe[0] = C * (2*f1 + f2);
    Fe[1] = C * (f1 + 2*f2);

    // Add boundary terms; Hughes p. 41, equation 1.13.12
    // Left hand boundary; e==0, adjust for u'(0) = h
    if (e == 0)
    {
        // Increment the force vector by the constraint h
        Fe[0] += h;
    }

    // Right hand boundary; e==n-1, adjust for u(1) = g
    if (e == (n-1))
    {
        // Compute K_element for this element
        double Ke[4];
        K_element_2(e, Ke);
        for (int a=0; a<2; ++a)
        {
            Fe[a] -= Ke[ij2k_elt(a,1)] * g;
        }
    }
}

// *********************************************************************************************************************
void PoissonFiniteElement::assemble_F()
{
    // Calculation will depend on the degrees of freedom, d
    // For now the only supported configuration is piecewise linear with d=2
    switch (d)
    {
        case 2:
            // Dispatch call to assemble_F_2
            assemble_F_2();
            break;
        default:
            string msg = (format("Error: degrees of frredom d=%i not supported.") % d).str();
            throw std::logic_error(msg);
    }
}

// *********************************************************************************************************************
void PoissonFiniteElement::assemble_F_2()
{
    // Local storage for F_element(e)
    double Fe[2];

    // Initialize an array for F of size n with all zeroes
    F = new double[n] {0.0};

    // Iterate over the first n-1 elements, which have the same treatment
    for (int e=0; e<n-1; ++e)
    {
        // Compute F_element for this element
        F_element_2(e, Fe);

        // Increment relevant entries in global F vector
        // Formula is at top of p. 44 in Hughes, equations 1.14.6 and 1.14.7
        // For all Hughes formulas, shift from 1-based to 0-based indexing

        // F[e] += F_element[1]
        F[e] += Fe[0];

        // F[e+1] += F_element[2]
        F[e+1] += Fe[1];
    }

    // Handle the last element, e=n-1; only the local node (e,e) contributes
    // See Hughes p. 43, equation 1.14.9.
    int e=n-1;
    F_element_2(e, Fe);
    F[e] += Fe[0];
}

// *********************************************************************************************************************
void PoissonFiniteElement::solve()
{
    // Allocate storage for U
    U = new double[n];

    // Need to solve the equation Ku = F
    // Copy the right hand side, F, into u because LAPACK routine overwrites it with the answer
    for (int i=0; i<n; ++i)
    {
        U[i] = F[i];
    }

    // Solve the equation with solve_matrix
    solve_matrix(n, K, U);
}

// *********************************************************************************************************************
// Print summary of problem setup
void PoissonFiniteElement::print_problem() const
{
    // Summarize this problem instance
    cout << format("Loaded 1D Poisson Problem from configuration file %1%.\n") % fname;
    cout << format("u(1)       g=%5.3f\n") % g;
    cout << format("u'(0)      h=%5.3f\n") % h;
    cout << format("mesh size  n=%i\n") % n;
    cout << format("DOF        d=%i\n") % d;
    cout << format("Quadrature q=%i\n") % q;

    // Print the f vector
    cout << format("\nf vector of %i elements:\n") % f.size();
    for (double f_e : f)
    {
        cout << format("%4.2f,  ") % f_e;
    }
    cout << "\n";

    // Print the x vector
    cout << format("\nx vector of %i nodes:\n") % x.size();
    for (double x_i : x)
    {
        cout << format("%4.2f,  ") % x_i;
    }
    cout << "\n";
}

// *********************************************************************************************************************
void PoissonFiniteElement::print_K() const
{
    cout << "\n";
    // Iterate over rows
    for (int i=0; i<n; ++i)
    {
        // Print each entry in row i
        for (int j=0; j<n; ++j)
        {
            cout << format("%5.2f ") % K_ij(i , j);
        }
        cout << "\n";
    }
}

// *********************************************************************************************************************
void PoissonFiniteElement::print_F() const
{
    cout << "\n";
    // Iterate over rows
    for (int i=0; i<n; ++i)
    {
        cout << format("%5.2f ") % F[i];
        cout << "\n";
    }
}

// *********************************************************************************************************************
void PoissonFiniteElement::print_U() const
{
    cout << "\n";
    // Iterate over rows
    for (int i=0; i<n; ++i)
    {
        cout << format("%5.2f ") % U[i];
        cout << "\n";
    }
    // Print the value at x=1 given by the constraint
    cout << format("%5.2f ") % g;
}
