# *************************************************************************************************
# Set environment
# *************************************************************************************************
# Include the configuration file
include config.mk

# Include the file dependencies
include Makefile.dep

# *************************************************************************************************
# Source, object and executable files
# *************************************************************************************************
# List of C++ source files; filename.cpp.  Includes both executables and intermediates.
SRC_CPP = $(wildcard *.cpp)

# Lists of object files; filename.o
OBJ := $(patsubst %.cpp, %.o, $(SRC_CPP))

# Lists of executables (prefix only)
EXEC := poisson

# List of executables (with .x suffix)
EXEC_X=$(patsubst %, %.x, $(EXEC))

# *************************************************************************************************
# Convenience targets: all, clean, default
# *************************************************************************************************
# Define target "all" to build all executables
all: $(EXEC)

# Define target "clean" to remove all the built files
clean:
	rm -f $(OBJ) $(EXEC_X)

# Set default goal to all
.DEFAULT_GOAL := all

# The PHONY command tells GNU Make than "clean" is a phony target, which means
# that it doesn't correspond to an actual file called "clean'.
.PHONY: clean

# *************************************************************************************************
# Rules to build object and executable filess
# *************************************************************************************************
# Build object files from source (including executables)
%.o: %.cpp
	$(CXX) $(CXX_OUT_OBJ) $(CXX_FLAGS) $(INCLUDE) \$(NEWLINE)

# Link executables from object files
$(EXEC): $(OBJ)
	$(CXX) $(CXX_OUT_EXE) $(CXX_FLAGS) $(LD_FLAGS) $(LD_LIBS) \$(NEWLINE)
