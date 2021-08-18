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

#ifndef __NX_REMOTE_HPP__
#define __NX_REMOTE_HPP__

#include <grpcpp/grpcpp.h>

#include "nexus.grpc.pb.h"

#include "nx_device.hpp"

namespace Nexus {

    class NXRemote final : public NexusRPC::NXService::Service
    {
    public:

        // =====================================================================
        // Constructor
        // =====================================================================

        explicit NXRemote(NXDevice * device) : m_device(device) {}

        // =====================================================================
        // RPC Implementations
        // =====================================================================

        grpc::Status ControlGetIdentity (
                  grpc::ServerContext         * ctx,
            const google::protobuf::Empty     * request,
                  NexusRPC::NXControlIdentity * response
        ) override;

        grpc::Status ControlSetReset (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  google::protobuf::Empty * response
        ) override;

        grpc::Status ControlGetParameters (
                  grpc::ServerContext           * ctx,
            const google::protobuf::Empty       * request,
                  NexusRPC::NXControlParameters * response
        ) override;

        grpc::Status ControlGetStatus (
                  grpc::ServerContext       * ctx,
            const google::protobuf::Empty   * request,
                  NexusRPC::NXControlStatus * response
        ) override;

        grpc::Status ControlGetCycles (
                  grpc::ServerContext       * ctx,
            const google::protobuf::Empty   * request,
                  NexusRPC::NXControlCycles * response
        ) override;

        grpc::Status ControlSetInterval (
                  grpc::ServerContext         * ctx,
            const NexusRPC::NXControlInterval * request,
                  google::protobuf::Empty     * response
        ) override;

        grpc::Status ControlSetActive (
                  grpc::ServerContext       * ctx,
            const NexusRPC::NXControlActive * request,
                  google::protobuf::Empty   * response
        ) override;

        grpc::Status MeshLoadInstruction (
                  grpc::ServerContext             * ctx,
            const NexusRPC::NXMeshLoadInstruction * request,
                  google::protobuf::Empty         * response
        ) override;

        grpc::Status MeshMapOutput (
                  grpc::ServerContext       * ctx,
            const NexusRPC::NXMeshMapOutput * request,
                  google::protobuf::Empty   * response
        ) override;

        grpc::Status MeshSetInput (
                  grpc::ServerContext         * ctx,
            const NexusRPC::NXMeshSignalState * request,
                  google::protobuf::Empty     * response
        ) override;

        grpc::Status MeshGetOutputState (
                  grpc::ServerContext         * ctx,
            const google::protobuf::Empty     * request,
                  NexusRPC::NXMeshOutputState * response
        ) override;

    private:
        // =====================================================================
        // Members
        // =====================================================================

        NXDevice * m_device;

    };

}

#endif // __NX_REMOTE_HPP__
