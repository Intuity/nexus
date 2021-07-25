#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>

typedef enum {
    NX_CTRL_RD_ID = 0,
    NX_CTRL_RD_VERSION,
    NX_CTRL_RD_PARAM,
    NX_CTRL_WR_ACTIVE,
    NX_CTRL_RD_STATUS,
    NX_CTRL_RD_CYCLES,
    NX_CTRL_WR_INTERVAL
} nx_ctrl_cmd_t;

typedef enum {
    NX_CTRL_PRM_CNTR_W = 0,
    NX_CTRL_PRM_ROWS,
    NX_CTRL_PRM_COLUMNS,
    NX_CTRL_PRM_ND_INS,
    NX_CTRL_PRM_ND_OUTS,
    NX_CTRL_PRM_ND_REGS
} nx_ctrl_prm_t;

int main(int argc, char * argv [])
{
    // Identify the device
    char * devname_h2c = "/dev/xdma0_h2c_0";
    char * devname_c2h = "/dev/xdma0_c2h_0";
    // Open a handle
    int fpga_wr = open(devname_h2c, O_RDWR);
    int fpga_rd = open(devname_c2h, O_RDWR);
    if (fpga_wr < 0) {
        fprintf(
            stderr,
            "Failed to open device %s -> %d\n",
            devname_h2c, fpga_wr
        );
        return 1;
    }
    if (fpga_rd < 0) {
        fprintf(
            stderr,
            "Failed to open device %s -> %d\n",
            devname_c2h, fpga_rd
        );
        return 1;
    }
    // Create a buffer
    uint64_t size = 32;
    char * tx_buff = NULL;
    char * rx_buff = NULL;
    posix_memalign((void **)&tx_buff, 4096, size + 4096);
    posix_memalign((void **)&rx_buff, 4096, size + 4096);
    if (!tx_buff) {
        fprintf(
            stderr,
            "Failed to allocate Tx buffer\n"
        );
        return 1;
    }
    if (!rx_buff) {
        fprintf(
            stderr,
            "Failed to allocate Rx buffer\n"
        );
        return 1;
    }

    // Map 32-bit integers to the buffer
    uint32_t * tx_slots = (uint32_t *)tx_buff;
    uint32_t   to_send  = 0;
    tx_slots[0] = (
        ((1             & 0x1) << 31) | // Control plane marker
        ((NX_CTRL_RD_ID & 0x7) << 28) | // Control command
        ((0                  ) <<  0)   // Payload
    );
    to_send += 1;
    tx_slots[1] = (
        ((1                  & 0x1) << 31) | // Control plane marker
        ((NX_CTRL_RD_VERSION & 0x7) << 28) | // Control command
        ((0                       ) <<  0)   // Payload
    );
    to_send += 1;
    for (uint32_t i = NX_CTRL_PRM_CNTR_W; i <= NX_CTRL_PRM_ND_REGS; i++) {
        tx_slots[2+i] = (
            ((1                & 0x1) << 31) | // Control plane marker
            ((NX_CTRL_RD_PARAM & 0x7) << 28) | // Control command
            ((i                & 0x7) << 25) | // Parameter type
            ((0                     ) <<  0)   // Payload
        );
        to_send += 1;
    }

    // Tx/Rx in a loop
    ssize_t total = 0;
    for (uint32_t i = 0; i < to_send; i++) {
        // Seek to start of target buffer
        ssize_t rc;
        rc = lseek(fpga_wr, 0, SEEK_SET);
        if (rc != 0) {
            fprintf(stderr, "Seek to 0 failed - %li\n", rc);
            return 1;
        }
        // Write next message
        rc = write(fpga_wr, (char *)&tx_slots[i], 4);
        if (rc < 0) {
            fprintf(stderr, "Write %u failed - %li\n", i, rc);
            return 1;
        }
        // Seek to start of source buffer
        rc = lseek(fpga_rd, 0, SEEK_SET);
        if (rc != 0) {
            fprintf(stderr, "Seek to 0 failed - %li\n", rc);
            return 1;
        }
        // Read next message
        rc = read(fpga_rd, &rx_buff[total], 4);
        if (rc < 0) {
            fprintf(stderr, "Read %u failed - %li\n", i, rc);
            return 1;
        }
        total += rc;
    }
    // Count total data transfer
    printf("Read back a total of %li bytes\n", total);

    // Print out the received words
    uint32_t * rx_slots = (uint32_t *)rx_buff;
    for (uint32_t i = 0; i < (total / 4); i++) {
        uint32_t dcd = rx_slots[i] & 0x7FFFFFFF;
        printf("Rx %3u -> 0x%08x (%u)\n", i, rx_slots[i], dcd);
    }

    return 0;
}
