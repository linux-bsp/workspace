cmake_minimum_required(VERSION 3.16)
project(bmctool VERSION 1.0.0 LANGUAGES C)

include(GNUInstallDirs)
find_package(Threads REQUIRED)

option(BMC_REDFISH "Build Redfish backend" ON)
option(BMC_IPMI "Build IPMI backend" OFF)
option(BMC_PMCP "Build PMCP backend" OFF)
option(BMC_REDFISH_VENDOR_SUPERMICRO "Build Supermicro Redfish support" ON)
option(BMC_REDFISH_VENDOR_XFUSION "Build xFusion Redfish support" ON)

if(NOT BMC_REDFISH AND NOT BMC_IPMI AND NOT BMC_PMCP)
    message(FATAL_ERROR "Enable at least one BMC backend")
endif()

add_library(bmctool SHARED src/pdi_bmc.c)
target_compile_features(bmctool PRIVATE c_std_99)
target_include_directories(bmctool PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)
target_link_libraries(bmctool PRIVATE Threads::Threads)
set_target_properties(bmctool PROPERTIES VERSION ${PROJECT_VERSION} SOVERSION 1)

if(BMC_REDFISH OR BMC_IPMI)
    find_package(PkgConfig REQUIRED)
endif()

if(BMC_REDFISH)
    pkg_check_modules(LIBCURL REQUIRED IMPORTED_TARGET libcurl)
    pkg_check_modules(CJSON QUIET IMPORTED_TARGET libcjson)
    if(NOT CJSON_FOUND)
        pkg_check_modules(CJSON REQUIRED IMPORTED_TARGET cjson)
    endif()
    target_compile_definitions(bmctool PRIVATE BMCTOOL_REDFISH)
    target_sources(bmctool PRIVATE
        src/pdi_curl.c
        src/redfish/pdi_bmc_redfish.c
        src/redfish/pdi_bmc_redfish_vendor.c
    )
    target_include_directories(bmctool PRIVATE src)
    target_link_libraries(bmctool PRIVATE PkgConfig::LIBCURL PkgConfig::CJSON)
    if(BMC_REDFISH_VENDOR_SUPERMICRO)
        target_compile_definitions(bmctool PRIVATE BMCTOOL_REDFISH_VENDOR_SUPERMICRO)
        target_sources(bmctool PRIVATE src/redfish/pdi_bmc_redfish_vendor_supermicro.c)
    endif()
    if(BMC_REDFISH_VENDOR_XFUSION)
        target_compile_definitions(bmctool PRIVATE BMCTOOL_REDFISH_VENDOR_XFUSION)
        target_sources(bmctool PRIVATE src/redfish/pdi_bmc_redfish_vendor_xfusion.c)
    endif()
endif()

if(BMC_IPMI)
    pkg_check_modules(FREEIPMI REQUIRED IMPORTED_TARGET libfreeipmi)
    target_compile_definitions(bmctool PRIVATE BMCTOOL_IPMI)
    target_sources(bmctool PRIVATE src/ipmi/pdi_bmc_ipmi.c src/ipmi/pdi_bmc_ipmi_vendor.c)
    target_link_libraries(bmctool PRIVATE PkgConfig::FREEIPMI)
endif()

if(BMC_PMCP)
    target_compile_definitions(bmctool PRIVATE BMCTOOL_PMCP)
    target_sources(bmctool PRIVATE src/pmcp/pdi_bmc_pmcp.c)
endif()

install(TARGETS bmctool LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
