cmake_minimum_required( VERSION 3.1.0 FATAL_ERROR )

if ( "${C_SDK_ROOT}" STREQUAL "" )
  set ( C_SDK_ROOT "/sdk" )
endif ( )

message("Using C SDK from ${C_SDK_ROOT}" )

set(use_edge_modules ON CACHE BOOL "include edge module code")
set(BUILD_SSL OFF CACHE BOOL "use SSL for restbed server")

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DHORTON_COMPILER=\"${CMAKE_CXX_COMPILER_ID}_${CMAKE_CXX_COMPILER_VERSION}_${CMAKE_BUILD_TYPE}\"")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DHORTON_COMPILER=\"${CMAKE_C_COMPILER_ID}_${CMAKE_C_COMPILER_VERSION}_${CMAKE_BUILD_TYPE}\"")

add_subdirectory( "${C_SDK_ROOT}" azure-iot-sdk-c )
add_subdirectory( "${PROJECT_SOURCE_DIR}/deps/restbed/" )

include_directories("${C_SDK_ROOT}/deps/parson") #this brings in parson from the source
include_directories(.)
include_directories(./generated)
include_directories(./glue)
include_directories(${SHARED_UTIL_INC_FOLDER})
include_directories(${IOTHUB_SERVICE_CLIENT_INC_FOLDER})
include_directories(${IOTHUB_CLIENT_INC_FOLDER})
include_directories("${PROJECT_SOURCE_DIR}/deps/restbed/source")
include_directories(${MACRO_UTILS_INC_FOLDER})
include_directories(${UMOCK_C_INC_FOLDER})

set(iothub_client_libs
    iothub_client
    iothub_service_client
    aziotsharedutil
    parson
)

if(${use_amqp})
    set(iothub_client_libs
        ${iothub_client_libs}
        iothub_client_amqp_transport
        uamqp
    )
endif()


if(${use_mqtt})
    set(iothub_client_libs
        ${iothub_client_libs}
        iothub_client_mqtt_transport
    )
endif()

if(${use_http})
    set(iothub_client_libs
        ${iothub_client_libs}
        iothub_client_http_transport
    )
endif()


set(generated_cpp_files
    generated/ModuleApi.cpp
    generated/ControlApi.cpp
    generated/RegistryApi.cpp
    generated/ServiceApi.cpp
    generated/DeviceApi.cpp
)

set(generated_h_files
    generated/ModuleApi.h
    generated/ControlApi.h
    generated/RegistryApi.h
    generated/ServiceApi.h
    generated/DeviceApi.h
)

set(glue_cpp_files
    glue/GlueUtils.cpp
    glue/InternalGlue.cpp
    glue/DeviceGlue.cpp
    glue/ModuleGlue.cpp
    glue/ControlGlue.cpp
    glue/json.cpp
)

set(glue_h_files
    glue/GlueUtils.h
    glue/InternalGlue.h
    glue/DeviceGlue.h
    glue/ModuleGlue.h
    glue/ControlGlue.h
    glue/json.h
    glue/iothub_sdk.h
)

add_executable(edge_e2e_rest_server
    main.cpp
    ${generated_cpp_files}
    ${generated_h_files}
    ${glue_cpp_files}
    ${glue_h_files}
)

target_link_libraries(edge_e2e_rest_server
    ${iothub_client_libs}
    restbed-static
)

