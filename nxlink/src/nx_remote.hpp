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

namespace Nexus {

    class NXRemote final : public NexusRPC::NXService::Service
    {
        grpc::Status Identify (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  NexusRPC::NXIdentity    * response
        ) override {
            printf("Called Identify via RPC\n");
            response->set_device_id(0x123456);
            response->set_version_major(0);
            response->set_version_minor(1);
            return grpc::Status::OK;
        }

        grpc::Status Reset (
                  grpc::ServerContext     * ctx,
            const google::protobuf::Empty * request,
                  google::protobuf::Empty * response
        ) override {
            printf("Called Reset via RPC\n");
            return grpc::Status::OK;
        }

    };

}

#endif // __NX_REMOTE_HPP__
