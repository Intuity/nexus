// Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "nx_remote.hpp"

#define NX_REM_DBG(...) printf(__VA_ARGS__);

// Identify
// Return the device ID and version information on request
//
grpc::Status Nexus::NXRemote::Identify (
          grpc::ServerContext     * ctx,
    const google::protobuf::Empty * request,
          NexusRPC::NXIdentity    * response
) {
    NX_REM_DBG("Received Identity request\n");
    response->set_device_id(m_device->read_device_id());
    nx_version_t version = m_device->read_version();
    response->set_version_major(version.major);
    response->set_version_minor(version.minor);
    return grpc::Status::OK;
}

// Reset
// Trigger the device reset upon request
//
grpc::Status Nexus::NXRemote::Reset (
          grpc::ServerContext     * ctx,
    const google::protobuf::Empty * request,
          google::protobuf::Empty * response
) {
    NX_REM_DBG("Received Reset request\n");
    m_device->reset();
    return grpc::Status::OK;
}

// Parameters
// Read back all of the parameters from the device
//
grpc::Status Nexus::NXRemote::Parameters (
          grpc::ServerContext     * ctx,
    const google::protobuf::Empty * request,
          NexusRPC::NXParameters  * response
) {
    NX_REM_DBG("Received Parameters request\n");
    nx_parameters_t params = m_device->read_parameters();
    response->set_counter_width(params.counter_width);
    response->set_rows(params.rows);
    response->set_columns(params.columns);
    response->set_node_inputs(params.node_inputs);
    response->set_node_outputs(params.node_outputs);
    response->set_node_registers(params.node_registers);
    return grpc::Status::OK;
}

// Status
// Read back the device's current status
//
grpc::Status Nexus::NXRemote::Status (
          grpc::ServerContext     * ctx,
    const google::protobuf::Empty * request,
          NexusRPC::NXStatus      * response
) {
    NX_REM_DBG("Received Status request\n");
    nx_status_t status = m_device->read_status();
    response->set_active(status.active);
    response->set_seen_idle_low(status.seen_idle_low);
    response->set_first_tick(status.first_tick);
    response->set_interval_set(status.interval_set);
    return grpc::Status::OK;
}

// SetInterval
// Set the interval in terms of clock cycles
//
grpc::Status Nexus::NXRemote::SetInterval (
          grpc::ServerContext     * ctx,
    const NexusRPC::NXInterval    * request,
          google::protobuf::Empty * response
) {
    m_device->set_interval(request->interval());
    return grpc::Status::OK;
}

// SetActive
// Enable/disable the mesh
//
grpc::Status Nexus::NXRemote::SetActive (
          grpc::ServerContext     * ctx,
    const NexusRPC::NXActive      * request,
          google::protobuf::Empty * response
) {
    m_device->set_active(request->active());
    return grpc::Status::OK;
}
