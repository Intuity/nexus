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

        grpc::Status Identify (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  NexusRPC::NXIdentity    * response
        ) override;

        grpc::Status Reset (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  google::protobuf::Empty * response
        ) override;

        grpc::Status Parameters (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  NexusRPC::NXParameters  * response
        ) override;

        grpc::Status Status (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  NexusRPC::NXStatus      * response
        ) override;

        grpc::Status SetInterval (
                  grpc::ServerContext     * ctx,
            const NexusRPC::NXInterval    * request,
                  google::protobuf::Empty * response
        ) override;

        grpc::Status SetActive (
                  grpc::ServerContext     * ctx,
            const NexusRPC::NXActive      * request,
                  google::protobuf::Empty * response
        ) override;

    private:
        // =====================================================================
        // Members
        // =====================================================================

        NXDevice * m_device;

    };

}

#endif // __NX_REMOTE_HPP__
