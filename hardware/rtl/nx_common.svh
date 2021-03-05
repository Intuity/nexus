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

`ifndef __NX_COMMON_SVH__
`define __NX_COMMON_SVH__

`define DECLARE_DQ(X) m_``X``_d, m_``X``_q
`define RESET_Q(X, Y) m_``X``_q <= (Y)
`define FLOP_DQ(X) m_``X``_q <= m_``X``_d
`define INIT_D(X) m_``X``_d = m_``X``_q

`endif // __NX_COMMON_SVH__
