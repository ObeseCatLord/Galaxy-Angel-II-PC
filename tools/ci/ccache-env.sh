# Sourced by the release builds: compile through ccache, kept by the workflow between runs (actions/cache).
# CMake (3.17 and later) takes the launcher from the environment. The cache is keyed on file contents and the
# compiler's own binary, with paths relative to the checkout, so a later run (or a renamed repository) hits it.
export CCACHE_DIR="${CCACHE_DIR:-$GITHUB_WORKSPACE/.ccache}"
export CCACHE_BASEDIR="$GITHUB_WORKSPACE"
export CCACHE_COMPILERCHECK=content
export CCACHE_COMPRESS=1
export CCACHE_MAXSIZE="${CCACHE_MAXSIZE:-3G}"
export CCACHE_NOHASHDIR=1
# The engines use precompiled headers (with their unity builds): ccache takes them when clang leaves the build
# time out of the .pch and these checks are relaxed (its documented setup for precompiled headers).
export CCACHE_SLOPPINESS=pch_defines,time_macros,include_file_mtime,include_file_ctime
export CXXFLAGS="${CXXFLAGS:-} -Xclang -fno-pch-timestamp"
export CMAKE_C_COMPILER_LAUNCHER=ccache CMAKE_CXX_COMPILER_LAUNCHER=ccache
mkdir -p "$CCACHE_DIR"
ccache -z > /dev/null
