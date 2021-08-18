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

#define NX_REM_DBG(...) // printf(__VA_ARGS__)

// ControlGetIdentity
// Return the device ID and version information on request
//
grpc::Status Nexus::NXRemote::ControlGetIdentity (
          grpc::ServerContext         * ctx,
    const google::protobuf::Empty     * request,
          NexusRPC::NXControlIdentity * response
) {
    NX_REM_DBG("Received identity request\n");
    response->set_device_id(m_device->read_device_id());
    nx_version_t version = m_device->read_version();
    response->set_version_major(version.major);
    response->set_version_minor(version.minor);
    return grpc::Status::OK;
}

// ControlSetReset
// Trigger the device reset upon request
//
grpc::Status Nexus::NXRemote::ControlSetReset (
          grpc::ServerContext     * ctx,
    const google::protobuf::Empty * request,
          google::protobuf::Empty * response
) {
    NX_REM_DBG("Received reset request\n");
    m_device->reset();
    return grpc::Status::OK;
}

// ControlGetParameters
// Read back all of the parameters from the device
//
grpc::Status Nexus::NXRemote::ControlGetParameters (
          grpc::ServerContext           * ctx,
    const google::protobuf::Empty       * request,
          NexusRPC::NXControlParameters * response
) {
    NX_REM_DBG("Received parameters request\n");
    nx_parameters_t params = m_device->read_parameters();
    response->set_counter_width(params.counter_width);
    response->set_rows(params.rows);
    response->set_columns(params.columns);
    response->set_node_inputs(params.node_inputs);
    response->set_node_outputs(params.node_outputs);
    response->set_node_registers(params.node_registers);
    return grpc::Status::OK;
}

// ControlGetStatus
// Read back the device's current status
//
grpc::Status Nexus::NXRemote::ControlGetStatus (
          grpc::ServerContext       * ctx,
    const google::protobuf::Empty   * request,
          NexusRPC::NXControlStatus * response
) {
    NX_REM_DBG("Received status request\n");
    nx_status_t status = m_device->read_status();
    response->set_active(status.active);
    response->set_seen_idle_low(status.seen_idle_low);
    response->set_first_tick(status.first_tick);
    response->set_interval_set(status.interval_set);
    return grpc::Status::OK;
}

// ControlGetCycles
// Read back the device's current status
//
grpc::Status Nexus::NXRemote::ControlGetCycles (
          grpc::ServerContext       * ctx,
    const google::protobuf::Empty   * request,
          NexusRPC::NXControlCycles * response
) {
    NX_REM_DBG("Received cycles request\n");
    response->set_cycles(m_device->read_cycles());
    return grpc::Status::OK;
}

// ControlSetInterval
// Set the interval in terms of clock cycles
//
grpc::Status Nexus::NXRemote::ControlSetInterval (
          grpc::ServerContext         * ctx,
    const NexusRPC::NXControlInterval * request,
          google::protobuf::Empty     * response
) {
    NX_REM_DBG("Setting interval to %u\n", request->interval());
    m_device->set_interval(request->interval());
    return grpc::Status::OK;
}

// ControlSetActive
// Enable/disable the mesh
//
grpc::Status Nexus::NXRemote::ControlSetActive (
          grpc::ServerContext       * ctx,
    const NexusRPC::NXControlActive * request,
          google::protobuf::Empty   * response
) {
    NX_REM_DBG("Setting active to %u\n", request->active());
    m_device->set_active(request->active());
    return grpc::Status::OK;
}

// MeshLoadInstruction
// Load an instruction into a node in the mesh
//
grpc::Status Nexus::NXRemote::MeshLoadInstruction (
          grpc::ServerContext             * ctx,
    const NexusRPC::NXMeshLoadInstruction * request,
          google::protobuf::Empty         * response
) {
    NX_REM_DBG(
        "Received mesh load instruction - R: %u, C: %u, I: 0x%08x\n",
        request->row(), request->column(), request->encoded()
    );
    m_device->send_to_mesh(nx_build_mesh_load_instruction(
        request->row(), request->column(), request->encoded()
    ));
    return grpc::Status::OK;
}

// MeshMapOutput
// Submit a node output mapping message into the mesh
//
grpc::Status Nexus::NXRemote::MeshMapOutput (
          grpc::ServerContext       * ctx,
    const NexusRPC::NXMeshMapOutput * request,
          google::protobuf::Empty   * response
) {
    nx_output_map_t mapping = {
        .index             = request->index(),
        .target_row        = request->target_row(),
        .target_column     = request->target_column(),
        .target_index      = request->target_index(),
        .target_sequential = request->target_sequential()
    };
    NX_REM_DBG(
        "Received mesh map output - R: %u, C: %u, I: %u TR: %u, TC: %u, TI: %u,"
        " TS: %u\n", request->row(), request->column(), mapping.index,
        mapping.target_row, mapping.target_column, mapping.target_index,
        mapping.target_sequential
    );
    m_device->send_to_mesh(nx_build_mesh_map_output(
        request->row(), request->column(), mapping
    ));
    return grpc::Status::OK;
}

// MeshSetInput
// Submit a signal state update into the mesh
//
grpc::Status Nexus::NXRemote::MeshSetInput (
          grpc::ServerContext         * ctx,
    const NexusRPC::NXMeshSignalState * request,
          google::protobuf::Empty     * response
) {
    nx_signal_state_t state = {
        .index      = request->index(),
        .sequential = request->sequential(),
        .value      = request->value()
    };
    m_device->send_to_mesh(nx_build_mesh_signal_state(
        request->row(), request->column(), state
    ));
    return grpc::Status::OK;
}

// MeshGetOutputState
// Get the current output state
//
grpc::Status Nexus::NXRemote::MeshGetOutputState (
          grpc::ServerContext         * ctx,
    const google::protobuf::Empty     * request,
          NexusRPC::NXMeshOutputState * response
) {
    response->set_state(m_device->get_output_state());
    return grpc::Status::OK;
}
