#!/usr/bin/env python

import os
import re
import sys
import time
import math
import getopt

def usage():
    print >> sys.stderr, "Usage:",sys.argv[0],"-g stl_file -s px,py,pz -e px,py,pz [-o vtk_file] [-p vtk_file]"
    print >> sys.stderr, "Options:"
    print >> sys.stderr, "\t-g stl_file"
    print >> sys.stderr, "\t--geometry stl_file"
    print >> sys.stderr, "\t\tSpecifies the STL file."
    print >> sys.stderr, ""
    print >> sys.stderr, "\t-o vtk_file"
    print >> sys.stderr, "\t--output vtk_file"
    print >> sys.stderr, "\t\tSpecifies the VTK file containing the preprocessing output."
    print >> sys.stderr, "\t\tIf this option is not set the out_file defaults to the name"
    print >> sys.stderr, "\t\tof the stl_file with '.vtk' appended."
    print >> sys.stderr, ""
    print >> sys.stderr, "\t-p vtk_file"
    print >> sys.stderr, "\t--preproc vtk_file"
    print >> sys.stderr, "\t\tSpecifies VTK preprocessing file generated by a previous"
    print >> sys.stderr, "\t\trun of this program. Specifying this file saves preprocessing"
    print >> sys.stderr, "\t\ttime."
    print >> sys.stderr, ""
    print >> sys.stderr, "\t-s px,py,pz"
    print >> sys.stderr, "\t--startp px,py,pz"
    print >> sys.stderr, "\t\tSpecifies a starting point for the generation of the centerlines."
    print >> sys.stderr, "\t\tThis option must be repeated for every starting point."
    print >> sys.stderr, ""
    print >> sys.stderr, "\t-e px,py,pz"
    print >> sys.stderr, "\t--endp px,py,pz"
    print >> sys.stderr, "\t\tSpecifies an endig point for the generation of the centerlines"
    print >> sys.stderr, "\t\tThis option must be repeated for every ending point."

def find4PSpCenter(points):

    p0 = points[0]
    p1 = points[1]
    p2 = points[2]
    p3 = points[3]

    l0 = p0[0]**2+p0[1]**2+p0[2]**2
    l1 = p1[0]**2+p1[1]**2+p1[2]**2
    l2 = p2[0]**2+p2[1]**2+p2[2]**2
    l3 = p3[0]**2+p3[1]**2+p3[2]**2

    m11 = vtk.vtkMatrix4x4.Determinant((p0[0], p0[1], p0[2], 1.0,
                        p1[0], p1[1], p1[2], 1.0,
                        p2[0], p2[1], p2[2], 1.0,
                        p3[0], p3[1], p3[2], 1.0))

    # no sphere passes across the four points...
    if math.fabs(m11-0.0) < (1.0E-10): return None

    m12 = vtk.vtkMatrix4x4.Determinant((l0, p0[1], p0[2], 1.0,
                        l1, p1[1], p1[2], 1.0,
                        l2, p2[1], p2[2], 1.0,
                        l3, p3[1], p3[2], 1.0))

    m13 = vtk.vtkMatrix4x4.Determinant((l0, p0[0], p0[2], 1.0,
                        l1, p1[0], p1[2], 1.0,
                        l2, p2[0], p2[2], 1.0,
                        l3, p3[0], p3[2], 1.0))

    m14 = vtk.vtkMatrix4x4.Determinant((l0, p0[0], p0[1], 1.0,
                        l1, p1[0], p1[1], 1.0,
                        l2, p2[0], p2[1], 1.0,
                        l3, p3[0], p3[1], 1.0))

    return 0.5*(m12/m11), -0.5*(m13/m11), 0.5*(m14/m11)

def dist2(n, m):
    return (n[0]-m[0])**2 + (n[1]-m[1])**2 + (n[2]-m[2])**2

STLFNAME = ''
OUTFNAME = ''
PPROCFNAME = ''
STAPOINTS = []
ENDPOINTS = []

opts, args = getopt.getopt(sys.argv[1:], "g:o:s:e:p:", ["geometry=","output=","startp=","endp=","preproc="])
if not opts:
    usage()
    sys.exit(1)
for o, a in opts:
    if o in ("-g", "--geometry"):
            STLFNAME = a
    elif o in ("-o", "--output"):
        OUTFNAME = a
    elif o in ("-p", "--preproc"):
        PPROCFNAME = a
    elif o in ("-s", "--startp", "-e", "--endp"):
        point = re.split('[ ]*,[ ]*', a.strip())
        point = filter(lambda x:x, point)
        try:
            point = tuple(float(coo) for coo in point)
        except ValueError:
            print >> sys.stderr, 'Bad point specification:', a, '\n'
            usage()
            sys.exit(1)
        if len(point) != 3:
            print >> sys.stderr, 'Bad number of coordinates for point:', a, '\n'
            usage()
            sys.exit(1)
        if o in ("-s", "--startp"):
            STAPOINTS.append(point)
        else:
            ENDPOINTS.append(point)
    else:
        usage()
        sys.exit(1)

# check for option consistency...
if not STLFNAME and not PPROCFNAME:
    print >> sys.stderr, 'Either geometry or preprocessing file must be specified.'
    usage()
    sys.exit(1)

if STLFNAME:
    if not os.path.isfile(STLFNAME):
        print >> sys.stderr, 'Cannot find file', STLFNAME
        sys.exit(1)

if PPROCFNAME:
    if not os.path.isfile(PPROCFNAME):
        print >> sys.stderr, 'Cannot find file', PPROCFNAME
        sys.exit(1)

if not OUTFNAME:
    OUTFNAME = STLFNAME if not PPROCFNAME else PPROCFNAME
    OUTFNAME = os.path.basename(OUTFNAME)
    OUTFNAME = OUTFNAME[:OUTFNAME.rfind('.')]

# moved here to pay import latency after parameters checking
from myvtk import *

start_time = time.time()
if not PPROCFNAME:
    print >> sys.stderr, "Computing Delaunay 3D triangulation...",
    dela_time = time.time()
    
    stl = vtk.vtkSTLReader()
    stl.SetFileName(STLFNAME)
    
    vtk.vtkDelaunay3D.GlobalWarningDisplayOff()
    dela = vtk.vtkDelaunay3D()
    dela.SetInputConnection(stl.GetOutputPort())
    dela.Update()
    
    print >> sys.stderr, "done", time.time()-dela_time, "secs"
    
    delaOut = dela.GetOutput()
    
    # Uncomment to write Delaunay VTK output
    #dsw = vtk.vtkUnstructuredGridWriter()
    #dsw.SetInputConnection(dela.GetOutputPort())
    #dsw.SetFileName('test.vtk')
    #dsw.Write()
    
    ncells = delaOut.GetNumberOfCells()
    
    vorNgh = dict()
    vorPts = vtk.vtkPoints()
    
    print >> sys.stderr, "Computing Voronoi cells centers and connectivity...",
    voro_time = time.time()
    
    center_time = 0
    neigh_time = 0
    for c in range(ncells):
        cell = delaOut.GetCell(c)
        if cell.GetCellType() != vtk.VTK_TETRA:
            print 'Found a cell that is not a Tetrahedron!'
            continue
    
        points = cell.GetPoints()
        points = [points.GetPoint(i) for i in range(points.GetNumberOfPoints())]
    
        center = find4PSpCenter(points)
        if not center: continue
    
        vorPts.InsertNextPoint(center)
    
        pointsIds = cell.GetPointIds()
        #print 'Current tetra points IDs of cell', str(c)+':',
        #    [pointsIds.GetId(i) for i in range(pointsIds.GetNumberOfIds())]
    
        # find neighboring cells
        facePts  = vtk.vtkIdList()
        ncellIds = vtk.vtkIdList()
    
        vorNgh[c] = []
        for f in range(4):
    
            # neighbor face
            facePts.DeepCopy(pointsIds)
            facePts.DeleteId(pointsIds.GetId(f))
            #print '\tcurrent face:', [facePts.GetId(i) for i in range(facePts.GetNumberOfIds())]
    
            # cells sharing neigh face
            delaOut.GetCellNeighbors(c, facePts, ncellIds)
            #print '\tcells sharing face:', [ncellIds.GetId(i) for i in range(ncellIds.GetNumberOfIds())], '\n'
            
            if ncellIds.GetNumberOfIds() > 1:
                print 'Cell', c, 'has more than one neighbor with face', f
                continue
    
            # if there is a single neighbor register the connection
            # only if its Id is greater than c
            if ncellIds.GetNumberOfIds() == 1:
                if c < ncellIds.GetId(0):
                    vorNgh[c].append(ncellIds.GetId(0))
            # nothing to do for faces with zero neighnors
    
    print >> sys.stderr, "done", time.time()-voro_time, "secs"
    
    # vorPts: points of ids [0,...,DelaCells-1]
    # vorNgh: dictionary, vorNgh[Id] contains all the points with id greater than Id
    #         connected with Id.
    
    pointsPolydata = vtk.vtkPolyData()
    pointsPolydata.SetPoints(vorPts);
    
    # Uncomment this to write the VTK file with all points and segnemnt
    # in the Voronoi diagram
    #segmCells = vtk.vtkCellArray()
    #for i in range(vorPts.GetNumberOfPoints()):
    #    for j in vorNgh[i]:
    #        line = vtk.vtkLine()
    #        line.GetPointIds().SetId(0,i)
    #        line.GetPointIds().SetId(1,j)
    #        segmCells.InsertNextCell(line)
    #
    #pointsPolydata.SetLines(segmCells)
    #pdw = vtk.vtkPolyDataWriter()
    #pdw.SetInput(pointsPolydata) 
    #pdw.SetFileName('test_segments.vtk')
    #pdw.Write()
    
    # select points inside/outside surface
    print >> sys.stderr, "Differentiating internal and external Voronoi points...",
    select_time = time.time()
    select = vtk.vtkSelectEnclosedPoints()

    if vtk.VTK_MAJOR_VERSION <= 5:
        select.SetInput(pointsPolydata)
        select.SetSurface(stl.GetOutput())
    else:
        select.SetInputData(pointsPolydata)
        select.SetSurfaceData(stl.GetOutput())

    select.SetTolerance(0.0000)
    select.Update()
    print >> sys.stderr, "done", time.time()-select_time, "secs"
    
    # compute mapping from global point id to internal point id
    print >> sys.stderr, "Generating polygonal data for internal Voronoi edges...",
    vedjes_time = time.time()
    idGlob2Int = [0]*vorPts.GetNumberOfPoints()
    idGlob2Int[0] = 0 if select.IsInside(0) else -1
    for pid in range(1, vorPts.GetNumberOfPoints()):
        if select.IsInside(pid):
            idGlob2Int[pid] = idGlob2Int[pid-1]+1
        else:
            idGlob2Int[pid] = idGlob2Int[pid-1]
    # idGlob2Int maps Ids of internal points to the range [0,...,# of intPoints -1]
    # for external points its value is undefined
    
    # copy internal points, their id will be in [0,...,# of intPoints -1]
    intVorPts = vtk.vtkPoints()
    for pid in range(vorPts.GetNumberOfPoints()):
        if select.IsInside(pid):
            intVorPts.InsertNextPoint(vorPts.GetPoint(pid))
    
    # We'll use the BSPTree to test if segments connecting
    # internal points traverse the surface
    bspTree = vtk.vtkModifiedBSPTree()
    bspTree.SetDataSet(stl.GetOutput());
    bspTree.BuildLocator()
    
    # params for IntersectWithLine
    tol = 0.001
    t = vtk.mutable(0.0)
    pInt = [0.0, 0.0, 0.0]
    pcoords = [0.0, 0.0, 0.0] # I can't find the meaning of this
    subId = vtk.mutable(0)
    
    # now generate the line cells connecting internal points
    intSegmCells = vtk.vtkCellArray()
    for pid in range(vorPts.GetNumberOfPoints()):
        
        # if point is external to the surface...
        if not select.IsInside(pid): continue
        if not pid in vorNgh: continue    # dela cells with 'None' centers do not 
                        # produce an entry in the vorNgh dict
        for nid in vorNgh[pid]:
            # if current neighbor is externel to the surface...
            if not select.IsInside(nid): continue
            # if the segment connecting pid and nid traverses the surface...
            if bspTree.IntersectWithLine(vorPts.GetPoint(pid), 
                             vorPts.GetPoint(nid), 
                             tol, t, pInt, pcoords, subId): continue
            # pid, nid and their segment are internal
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0,idGlob2Int[pid])
            line.GetPointIds().SetId(1,idGlob2Int[nid])
            intSegmCells.InsertNextCell(line)
                    
    finalPolyData = vtk.vtkPolyData()
    finalPolyData.SetPoints(intVorPts)
    finalPolyData.SetLines(intSegmCells)
    print >> sys.stderr, "done", time.time()-vedjes_time, "secs"
else:
    vorf = vtk.vtkPolyDataReader()
    vorf.SetFileName(PPROCFNAME)
    vorf.Update()
    finalPolyData = vorf.GetOutput()
    intVorPts = finalPolyData.GetPoints()

pdw = vtk.vtkPolyDataWriter()
if not PPROCFNAME:
    # write VTK file with whole internal Voronoi edges
    if vtk.VTK_MAJOR_VERSION <= 5:
        pdw.SetInput(finalPolyData) 
    else:
        pdw.SetInputData(finalPolyData) 
    pdw.SetFileName(OUTFNAME+'_voronoi.vtk')
    pdw.Write()
    
print >> sys.stderr, "Finding centerlines and writing files..."
center_time = time.time()

spointIDs  = [-1]*len(STAPOINTS)
epointIDs  = [-1]*len(ENDPOINTS)
spointDist = [sys.maxint]*len(STAPOINTS)
epointDist = [sys.maxint]*len(ENDPOINTS)

for pid in range(intVorPts.GetNumberOfPoints()):

    p = intVorPts.GetPoint(pid)

    for i in range(len(STAPOINTS)):

        d2 = dist2(p, STAPOINTS[i])

        if d2 < spointDist[i]:
            spointIDs[i] = pid
            spointDist[i] = d2

    for i in range(len(ENDPOINTS)):

        d2 = dist2(p, ENDPOINTS[i])

        if d2 < epointDist[i]:
            epointIDs[i] = pid
            epointDist[i] = d2
#print
#for i in range(len(STAPOINTS)):
#    print 'Nearest point of', STAPOINTS[i], 'is', intVorPts.GetPoint(spointIDs[i]), ', d =', spointDist[i], 'id =', spointIDs[i]
#for i in range(len(ENDPOINTS)):
#    print 'Nearest point of', ENDPOINTS[i], 'is', intVorPts.GetPoint(epointIDs[i]), ', d =', epointDist[i], 'id =', epointIDs[i]

lenArray = vtk.vtkDoubleArray()
dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
if vtk.VTK_MAJOR_VERSION <= 5:
    dijkstra.SetInput(finalPolyData)
else:
    dijkstra.SetInputData(finalPolyData)

print >> sys.stderr, "dijkstra...",STAPOINTS,ENDPOINTS
for s in range(len(STAPOINTS)):
    for e in range(len(ENDPOINTS)):
    
        dijkstra.SetEndVertex(spointIDs[s]) # going fron inlet to outlet SM
        dijkstra.SetStartVertex(epointIDs[e])

        # dijkstra.SetStartVertex(spointIDs[s]) # going fron outlet to inlet SM
        # dijkstra.SetEndVertex(epointIDs[e])

        dijkstra.Update()
        
        dijkstra.GetCumulativeWeights(lenArray)

        if lenArray.GetValue(epointIDs[s]) < 0.0: # end is not reachable from start
            print >> sys.stderr, "end is not reachable from start !!"
            continue
        
        print >> sys.stderr, "writing on file...", OUTFNAME+'.vtk'

        pdw.SetInputConnection(dijkstra.GetOutputPort())
        pdw.SetFileName(OUTFNAME+'.vtk')
        # pdw.SetFileName(OUTFNAME+'_'+str(s)+'-'+str(e)+'.vtk')
        pdw.Write()

        print >> sys.stderr, "...done writing on file"

print >> sys.stderr, "done", time.time()-center_time, "secs"
print >> sys.stderr, "Total time", time.time()-start_time, "secs"
sys.exit(0)
