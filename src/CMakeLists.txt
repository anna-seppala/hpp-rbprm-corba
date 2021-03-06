# Copyright (c) 2012 CNRS
# Author: Florent Lamiraux
#
# This file is part of hpp-rbprm-corba.
# hpp-rbprm-corba is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# hpp-rbprm-corba is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Lesser Public License for more details.  You should have
# received a copy of the GNU Lesser General Public License along with
# hpp-rbprm-corba.  If not, see
# <http://www.gnu.org/licenses/>.

SET(LIBRARY_NAME ${PROJECT_NAME})
SET(IDL_SOURCES
	rbprmbuilder
)

SET(HPP_CORBASERVER_IDL_SOURCES
  common
)

OMNIIDL_INCLUDE_DIRECTORIES(
  ${HPP_CORBASERVER_DATAROOTDIR}/idl ${CMAKE_SOURCE_DIR}/idl
  )

INCLUDE_DIRECTORIES(${CMAKE_BINARY_DIR}/src)
FOREACH(IDL ${IDL_SOURCES})
  GENERATE_IDL_FILE (${IDL}
    ${CMAKE_SOURCE_DIR}/idl/hpp/corbaserver/rbprm
    )
ENDFOREACH()

FOREACH(IDL ${HPP_CORBASERVER_IDL_SOURCES})
  GENERATE_IDL_FILE (${IDL}
    ${HPP_CORBASERVER_DATAROOTDIR}/idl/hpp/corbaserver
    )
ENDFOREACH()

ADD_LIBRARY(${LIBRARY_NAME} SHARED
  common.hh
  commonSK.cc
	rbprmbuilder.hh
	rbprmbuilderSK.cc
	rbprmbuilder.impl.cc
	rbprmbuilder.impl.hh
	server.cc
	${CMAKE_CURRENT_BINARY_DIR}/hpp/corbaserver/rbprm/rbprmbuilder_idl.py
	${CMAKE_CURRENT_BINARY_DIR}/hpp/corbaserver/rbprm/common_idl.py
)

PKG_CONFIG_USE_DEPENDENCY(${LIBRARY_NAME} hpp-rbprm)
PKG_CONFIG_USE_DEPENDENCY(${LIBRARY_NAME} hpp-model-urdf)
PKG_CONFIG_USE_DEPENDENCY(${LIBRARY_NAME} hpp-corbaserver)
PKG_CONFIG_USE_DEPENDENCY(${LIBRARY_NAME} omniORB4)
PKG_CONFIG_USE_DEPENDENCY(${LIBRARY_NAME} hpp-rbprm)

INSTALL(TARGETS ${LIBRARY_NAME} DESTINATION lib)

# search for python
FINDPYTHON()

# Generate and install python code for each idl file
FOREACH (IDL ${IDL_SOURCES})
  ADD_CUSTOM_COMMAND(
    OUTPUT
    ${CMAKE_CURRENT_BINARY_DIR}/hpp/corbaserver/rbprm/${IDL}_idl.py
    COMMAND ${OMNIIDL}
    ARGS -bpython -Wbpackage="" -I${CMAKE_SOURCE_DIR}/idl
    -I${HPP_CORBASERVER_DATAROOTDIR}/idl
    ${CMAKE_SOURCE_DIR}/idl/hpp/corbaserver/rbprm/${IDL}.idl
    MAIN_DEPENDENCY
    ${CMAKE_SOURCE_DIR}/idl/hpp/corbaserver/rbprm/${IDL}.idl
    )
  SET_SOURCE_FILES_PROPERTIES(
    ${CMAKE_CURRENT_BINARY_DIR}/${IDL}_idl.py
    GENERATED=ON
    )
  INSTALL(
    FILES
    ${CMAKE_CURRENT_BINARY_DIR}/${IDL}_idl.py
    DESTINATION ${PYTHON_SITELIB}/hpp/corbaserver/rbprm
    )
ENDFOREACH()

# Generate and install python code for each dependency idl file
FOREACH (IDL ${HPP_CORBASERVER_IDL_SOURCES})
  ADD_CUSTOM_COMMAND(
    OUTPUT
    ${CMAKE_CURRENT_BINARY_DIR}/hpp/corbaserver/rbprm/${IDL}_idl.py
    COMMAND ${OMNIIDL}
    ARGS -bpython -Wbpackage=""
    -I${HPP_CORBASERVER_DATAROOTDIR}/idl
    ${HPP_CORBASERVER_DATAROOTDIR}/idl/hpp/corbaserver/${IDL}.idl
    MAIN_DEPENDENCY
    ${HPP_CORBASERVER_DATAROOTDIR}/idl/hpp/corbaserver/${IDL}.idl
    )
  SET_SOURCE_FILES_PROPERTIES(
    ${CMAKE_CURRENT_BINARY_DIR}/${IDL}_idl.py
    GENERATED=ON
    )
  INSTALL(
    FILES
    ${CMAKE_CURRENT_BINARY_DIR}/${IDL}_idl.py
    DESTINATION ${PYTHON_SITELIB}/hpp/corbaserver/rbprm
    )
ENDFOREACH()

INSTALL(
  FILES
  ${CMAKE_CURRENT_SOURCE_DIR}/hpp/corbaserver/rbprm/__init__.py
  DESTINATION ${PYTHON_SITELIB}/hpp/corbaserver/rbprm
  )
INSTALL(
  FILES
	${CMAKE_CURRENT_SOURCE_DIR}/hpp/corbaserver/rbprm/client.py
	${CMAKE_CURRENT_SOURCE_DIR}/hpp/corbaserver/rbprm/rbprmbuilder.py
        ${CMAKE_CURRENT_SOURCE_DIR}/hpp/corbaserver/rbprm/rbprmfullbody.py
	${CMAKE_CURRENT_SOURCE_DIR}/hpp/corbaserver/rbprm/problem_solver.py
  DESTINATION ${PYTHON_SITELIB}/hpp/corbaserver/rbprm
  )

# Stand alone corba server
ADD_EXECUTABLE (hpp-rbprm-server hpp-rbprm-corba.cc)
TARGET_LINK_LIBRARIES (hpp-rbprm-server ${LIBRARY_NAME} hpp-rbprm)
PKG_CONFIG_USE_DEPENDENCY(hpp-rbprm-server hpp-model-urdf)

INSTALL (TARGETS hpp-rbprm-server DESTINATION ${CMAKE_INSTALL_BINDIR})
