compute:
    LOAD    0, 0, 0x003, PRESERVE            // @ 0x000 Loading R0 with state_1_q___X0, state_0_q___X0, -, -, -, -, -, -
    TRUTH   0, 0, 0, 1, 0, 0, 0x88           // @ 0x001 TT0 - (F:state_0_q___X0) & (F:state_1_q___X0) - state_0_q___X0, state_1_q___X0
    LOAD    1, 1, 0x002, PRESERVE            // @ 0x002 Loading R1 with sum_state_q___X0, state_1_q___X1, state_0_q___X1, sum_state_q___X7, -, sum_state_q___X6, -, sum_state_q___X5
    TRUTH   7, 1, 1, 0, 2, 1, 0xE8           // @ 0x003 TT1 - (<nx_gate_68_OR>) | (<nx_gate_69_AND>) - TT0, state_0_q___X1, state_1_q___X1
    LOAD    2, 0, 0x000, PRESERVE            // @ 0x004 Loading R2 with state_0_q___X13, state_0_q___X14, state_0_q___X15, -, -, state_0_q___X2, state_0_q___X3, state_0_q___X4
    LOAD    3, 1, 0x001, PRESERVE            // @ 0x005 Loading R3 with -, state_1_q___X2, state_1_q___X3, state_1_q___X4, state_1_q___X5, state_1_q___X6, state_1_q___X7, state_1_q___X8
    TRUTH   7, 2, 3, 0, 5, 1, 0xE8           // @ 0x006 TT2 - (<nx_gate_75_OR>) | (<nx_gate_76_AND>) - TT1, state_0_q___X2, state_1_q___X2
    TRUTH   7, 2, 3, 0, 6, 2, 0xE8           // @ 0x007 TT3 - (<nx_gate_82_OR>) | (<nx_gate_83_AND>) - TT2, state_0_q___X3, state_1_q___X3
    TRUTH   7, 2, 3, 0, 7, 3, 0xE8           // @ 0x008 TT4 - (<nx_gate_89_OR>) | (<nx_gate_90_AND>) - TT3, state_0_q___X4, state_1_q___X4
    LOAD    4, 1, 0x000, PRESERVE            // @ 0x009 Loading R4 with state_0_q___X5, state_0_q___X6, state_0_q___X7, state_0_q___X8, state_0_q___X9, state_0_q___X10, state_0_q___X11, state_0_q___X12
    TRUTH   7, 4, 3, 0, 0, 4, 0xE8           // @ 0x00A TT5 - (<nx_gate_96_OR>) | (<nx_gate_97_AND>) - TT4, state_0_q___X5, state_1_q___X5
    TRUTH   7, 4, 3, 0, 1, 5, 0xE8           // @ 0x00B TT60 - (<nx_gate_103_OR>) | (<nx_gate_104_AND>) - TT5, state_0_q___X6, state_1_q___X6
    TRUTH   0, 1, 0, 1, 2, 0, 0x88           // @ 0x00C TT6 - (F:state_0_q___X0) & (F:state_0_q___X1) - state_0_q___X0, state_0_q___X1
    SHUFFLE 7, 5, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x00D Copy 7 to 5
    TRUTH   7, 2, 0, 0, 5, 0, 0x88           // @ 0x00E TT7 - (<nx_gate_2_AND>) & (F:state_0_q___X2) - TT6, state_0_q___X2
    TRUTH   7, 2, 0, 0, 6, 0, 0x88           // @ 0x00F TT8 - (<nx_gate_4_AND>) & (F:state_0_q___X3) - TT7, state_0_q___X3
    TRUTH   7, 2, 0, 0, 7, 0, 0x88           // @ 0x010 TT9 - (<nx_gate_6_AND>) & (F:state_0_q___X4) - TT8, state_0_q___X4
    TRUTH   7, 4, 0, 0, 0, 0, 0x88           // @ 0x011 TT10 - (<nx_gate_8_AND>) & (F:state_0_q___X5) - TT9, state_0_q___X5
    TRUTH   7, 4, 0, 0, 1, 0, 0x88           // @ 0x012 TT11 - (<nx_gate_10_AND>) & (F:state_0_q___X6) - TT10, state_0_q___X6
    TRUTH   7, 4, 0, 0, 2, 0, 0x88           // @ 0x013 TT12 - (<nx_gate_12_AND>) & (F:state_0_q___X7) - TT11, state_0_q___X7
    TRUTH   7, 4, 0, 0, 3, 0, 0x88           // @ 0x014 TT13 - (<nx_gate_14_AND>) & (F:state_0_q___X8) - TT12, state_0_q___X8
    TRUTH   7, 4, 0, 0, 4, 0, 0x88           // @ 0x015 TT14 - (<nx_gate_16_AND>) & (F:state_0_q___X9) - TT13, state_0_q___X9
    SHUFFLE 7, 6, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x016 Copy 7 to 6
    TRUTH   7, 4, 0, 0, 5, 0, 0x88           // @ 0x017 TT15 - (<nx_gate_18_AND>) & (F:state_0_q___X10) - TT14, state_0_q___X10
    TRUTH   7, 4, 0, 0, 6, 0, 0x88           // @ 0x018 TT16 - (<nx_gate_20_AND>) & (F:state_0_q___X11) - TT15, state_0_q___X11
    TRUTH   7, 4, 0, 0, 7, 0, 0x88           // @ 0x019 TT17 - (<nx_gate_22_AND>) & (F:state_0_q___X12) - TT16, state_0_q___X12
    TRUTH   7, 2, 0, 0, 0, 0, 0x88           // @ 0x01A TT18 - (<nx_gate_24_AND>) & (F:state_0_q___X13) - TT17, state_0_q___X13
    TRUTH   7, 2, 0, 0, 1, 0, 0x88           // @ 0x01B TT32 - (<nx_gate_26_AND>) & (F:state_0_q___X14) - TT18, state_0_q___X14
    TRUTH   7, 2, 0, 0, 2, 0, 0x66           // @ 0x01C TT81 - (<nx_gate_28_AND>) ^ (F:state_0_q___X15) - TT32, state_0_q___X15
    TRUTH   7, 2, 0, 2, 1, 0, 0x66           // @ 0x01D TT80 - (<nx_gate_26_AND>) ^ (F:state_0_q___X14) - TT18, state_0_q___X14
    TRUTH   7, 2, 0, 4, 0, 0, 0x66           // @ 0x01E TT79 - (<nx_gate_24_AND>) ^ (F:state_0_q___X13) - TT17, state_0_q___X13
    SHUFFLE 7, 3, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x01F Copy 7 to 3
    STORE   7, 0x07, 0, 0x000, INVERSE       // @ 0x020 Flushing out state_0_q___X13, state_0_q___X14, state_0_q___X15
    TRUTH   7, 4, 0, 6, 7, 0, 0x66           // @ 0x021 TT78 - (<nx_gate_22_AND>) ^ (F:state_0_q___X12) - TT16, state_0_q___X12
    TRUTH   3, 4, 0, 7, 6, 0, 0x66           // @ 0x022 TT77 - (<nx_gate_20_AND>) ^ (F:state_0_q___X11) - TT15, state_0_q___X11
    TRUTH   6, 4, 0, 0, 5, 0, 0x66           // @ 0x023 TT76 - (<nx_gate_18_AND>) ^ (F:state_0_q___X10) - TT14, state_0_q___X10
    TRUTH   6, 4, 0, 1, 4, 0, 0x66           // @ 0x024 TT75 - (<nx_gate_16_AND>) ^ (F:state_0_q___X9) - TT13, state_0_q___X9
    TRUTH   6, 4, 0, 2, 3, 0, 0x66           // @ 0x025 TT74 - (<nx_gate_14_AND>) ^ (F:state_0_q___X8) - TT12, state_0_q___X8
    TRUTH   6, 4, 0, 3, 2, 0, 0x66           // @ 0x026 TT73 - (<nx_gate_12_AND>) ^ (F:state_0_q___X7) - TT11, state_0_q___X7
    TRUTH   6, 4, 0, 4, 1, 0, 0x66           // @ 0x027 TT72 - (<nx_gate_10_AND>) ^ (F:state_0_q___X6) - TT10, state_0_q___X6
    TRUTH   6, 4, 0, 5, 0, 0, 0x66           // @ 0x028 TT71 - (<nx_gate_8_AND>) ^ (F:state_0_q___X5) - TT9, state_0_q___X5
    STORE   3, 0xFF, 1, 0x003, SET_LOW       // @ 0x029
    SHUFFLE 7, 3, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x02A Copy 7 to 3
    STORE   7, 0xFF, 1, 0x000, INVERSE       // @ 0x02B Flushing out state_0_q___X5, state_0_q___X6, state_0_q___X7, state_0_q___X8, state_0_q___X9, state_0_q___X10, state_0_q___X11, state_0_q___X12
    TRUTH   6, 2, 0, 6, 7, 0, 0x66           // @ 0x02C TT70 - (<nx_gate_6_AND>) ^ (F:state_0_q___X4) - TT8, state_0_q___X4
    TRUTH   6, 2, 0, 7, 6, 0, 0x66           // @ 0x02D TT69 - (<nx_gate_4_AND>) ^ (F:state_0_q___X3) - TT7, state_0_q___X3
    TRUTH   5, 2, 0, 0, 5, 0, 0x66           // @ 0x02E TT68 - (<nx_gate_2_AND>) ^ (F:state_0_q___X2) - TT6, state_0_q___X2
    TRUTH   0, 1, 0, 0, 1, 0, 0x88           // @ 0x02F TT19 - (F:state_1_q___X0) & (F:state_1_q___X1) - state_1_q___X0, state_1_q___X1
    STORE   3, 0xFF, 1, 0x003, SET_HIGH      // @ 0x030
    LOAD    3, 1, 0x001, PRESERVE            // @ 0x031 Loading R3 with -, state_1_q___X2, state_1_q___X3, state_1_q___X4, state_1_q___X5, state_1_q___X6, state_1_q___X7, state_1_q___X8
    TRUTH   7, 3, 0, 0, 1, 0, 0x88           // @ 0x032 TT20 - (<nx_gate_33_AND>) & (F:state_1_q___X2) - TT19, state_1_q___X2
    TRUTH   7, 3, 0, 0, 2, 0, 0x88           // @ 0x033 TT21 - (<nx_gate_35_AND>) & (F:state_1_q___X3) - TT20, state_1_q___X3
    TRUTH   7, 3, 0, 0, 3, 0, 0x88           // @ 0x034 TT22 - (<nx_gate_37_AND>) & (F:state_1_q___X4) - TT21, state_1_q___X4
    TRUTH   7, 3, 0, 0, 4, 0, 0x88           // @ 0x035 TT23 - (<nx_gate_39_AND>) & (F:state_1_q___X5) - TT22, state_1_q___X5
    SHUFFLE 7, 6, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x036 Copy 7 to 6
    STORE   7, 0xE0, 0, 0x000, INVERSE       // @ 0x037 Flushing out state_0_q___X2, state_0_q___X3, state_0_q___X4
    TRUTH   7, 3, 0, 0, 5, 0, 0x88           // @ 0x038 TT24 - (<nx_gate_41_AND>) & (F:state_1_q___X6) - TT23, state_1_q___X6
    TRUTH   7, 3, 0, 0, 6, 0, 0x88           // @ 0x039 TT25 - (<nx_gate_43_AND>) & (F:state_1_q___X7) - TT24, state_1_q___X7
    TRUTH   7, 3, 0, 0, 7, 0, 0x88           // @ 0x03A TT26 - (<nx_gate_45_AND>) & (F:state_1_q___X8) - TT25, state_1_q___X8
    LOAD    0, 0, 0x001, PRESERVE            // @ 0x03B Loading R0 with state_1_q___X9, state_1_q___X10, state_1_q___X11, state_1_q___X12, state_1_q___X13, state_1_q___X14, state_1_q___X15, -
    TRUTH   7, 0, 0, 0, 0, 0, 0x88           // @ 0x03C TT27 - (<nx_gate_47_AND>) & (F:state_1_q___X9) - TT26, state_1_q___X9
    TRUTH   7, 0, 0, 0, 1, 0, 0x88           // @ 0x03D TT28 - (<nx_gate_49_AND>) & (F:state_1_q___X10) - TT27, state_1_q___X10
    TRUTH   7, 0, 0, 0, 2, 0, 0x88           // @ 0x03E TT29 - (<nx_gate_51_AND>) & (F:state_1_q___X11) - TT28, state_1_q___X11
    TRUTH   7, 0, 0, 0, 3, 0, 0x88           // @ 0x03F TT30 - (<nx_gate_53_AND>) & (F:state_1_q___X12) - TT29, state_1_q___X12
    TRUTH   7, 0, 0, 0, 4, 0, 0x88           // @ 0x040 TT31 - (<nx_gate_55_AND>) & (F:state_1_q___X13) - TT30, state_1_q___X13
    SHUFFLE 7, 4, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x041 Copy 7 to 4
    TRUTH   7, 0, 0, 0, 5, 0, 0x88           // @ 0x042 TT33 - (<nx_gate_57_AND>) & (F:state_1_q___X14) - TT31, state_1_q___X14
    TRUTH   7, 0, 0, 0, 6, 0, 0x66           // @ 0x043 TT97 - (<nx_gate_59_AND>) ^ (F:state_1_q___X15) - TT33, state_1_q___X15
    TRUTH   4, 0, 0, 0, 5, 0, 0x66           // @ 0x044 TT96 - (<nx_gate_57_AND>) ^ (F:state_1_q___X14) - TT31, state_1_q___X14
    TRUTH   4, 0, 0, 1, 4, 0, 0x66           // @ 0x045 TT95 - (<nx_gate_55_AND>) ^ (F:state_1_q___X13) - TT30, state_1_q___X13
    TRUTH   4, 0, 0, 2, 3, 0, 0x66           // @ 0x046 TT94 - (<nx_gate_53_AND>) ^ (F:state_1_q___X12) - TT29, state_1_q___X12
    TRUTH   4, 0, 0, 3, 2, 0, 0x66           // @ 0x047 TT93 - (<nx_gate_51_AND>) ^ (F:state_1_q___X11) - TT28, state_1_q___X11
    TRUTH   4, 0, 0, 4, 1, 0, 0x66           // @ 0x048 TT92 - (<nx_gate_49_AND>) ^ (F:state_1_q___X10) - TT27, state_1_q___X10
    TRUTH   4, 0, 0, 5, 0, 0, 0x66           // @ 0x049 TT91 - (<nx_gate_47_AND>) ^ (F:state_1_q___X9) - TT26, state_1_q___X9
    SHUFFLE 7, 0, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x04A Copy 7 to 0
    STORE   7, 0x7F, 0, 0x001, INVERSE       // @ 0x04B Flushing out state_1_q___X9, state_1_q___X10, state_1_q___X11, state_1_q___X12, state_1_q___X13, state_1_q___X14, state_1_q___X15
    TRUTH   4, 3, 0, 6, 7, 0, 0x66           // @ 0x04C TT90 - (<nx_gate_45_AND>) ^ (F:state_1_q___X8) - TT25, state_1_q___X8
    TRUTH   4, 3, 0, 7, 6, 0, 0x66           // @ 0x04D TT89 - (<nx_gate_43_AND>) ^ (F:state_1_q___X7) - TT24, state_1_q___X7
    TRUTH   6, 3, 0, 0, 5, 0, 0x66           // @ 0x04E TT88 - (<nx_gate_41_AND>) ^ (F:state_1_q___X6) - TT23, state_1_q___X6
    TRUTH   6, 3, 0, 1, 4, 0, 0x66           // @ 0x04F TT87 - (<nx_gate_39_AND>) ^ (F:state_1_q___X5) - TT22, state_1_q___X5
    TRUTH   6, 3, 0, 2, 3, 0, 0x66           // @ 0x050 TT86 - (<nx_gate_37_AND>) ^ (F:state_1_q___X4) - TT21, state_1_q___X4
    TRUTH   6, 3, 0, 3, 2, 0, 0x66           // @ 0x051 TT85 - (<nx_gate_35_AND>) ^ (F:state_1_q___X3) - TT20, state_1_q___X3
    TRUTH   6, 3, 0, 4, 1, 0, 0x66           // @ 0x052 TT84 - (<nx_gate_33_AND>) ^ (F:state_1_q___X2) - TT19, state_1_q___X2
    TRUTH   1, 1, 0, 2, 1, 0, 0x66           // @ 0x053 TT34 - (F:state_0_q___X1) ^ (F:state_1_q___X1) - state_0_q___X1, state_1_q___X1
    STORE   0, 0xFF, 0, 0x004, SET_LOW       // @ 0x054
    SHUFFLE 7, 0, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x055 Copy 7 to 0
    STORE   7, 0xFE, 1, 0x001, INVERSE       // @ 0x056 Flushing out state_1_q___X2, state_1_q___X3, state_1_q___X4, state_1_q___X5, state_1_q___X6, state_1_q___X7, state_1_q___X8
    TRUTH   5, 7, 0, 7, 0, 0, 0x66           // @ 0x057 TT99 - (<nx_gate_63_AND>) ^ (<nx_gate_64_XOR>) - TT0, TT34
    TRUTH   2, 3, 0, 5, 1, 0, 0x66           // @ 0x058 TT35 - (F:state_0_q___X2) ^ (F:state_1_q___X2) - state_0_q___X2, state_1_q___X2
    TRUTH   5, 7, 0, 6, 0, 0, 0x66           // @ 0x059 TT100 - (<nx_gate_70_OR>) ^ (<nx_gate_71_XOR>) - TT1, TT35
    TRUTH   2, 3, 0, 6, 2, 0, 0x66           // @ 0x05A TT40 - (F:state_0_q___X3) ^ (F:state_1_q___X3) - state_0_q___X3, state_1_q___X3
    TRUTH   5, 7, 0, 5, 0, 0, 0x66           // @ 0x05B TT101 - (<nx_gate_77_OR>) ^ (<nx_gate_78_XOR>) - TT2, TT40
    TRUTH   2, 3, 0, 7, 3, 0, 0x66           // @ 0x05C TT45 - (F:state_0_q___X4) ^ (F:state_1_q___X4) - state_0_q___X4, state_1_q___X4
    TRUTH   5, 7, 0, 4, 0, 0, 0x66           // @ 0x05D TT102 - (<nx_gate_84_OR>) ^ (<nx_gate_85_XOR>) - TT3, TT45
    STORE   0, 0xFF, 0, 0x004, SET_HIGH      // @ 0x05E
    LOAD    0, 1, 0x000, PRESERVE            // @ 0x05F Loading R0 with state_0_q___X5, state_0_q___X6, state_0_q___X7, state_0_q___X8, state_0_q___X9, state_0_q___X10, state_0_q___X11, state_0_q___X12
    TRUTH   0, 3, 0, 0, 4, 0, 0x66           // @ 0x060 TT50 - (F:state_0_q___X5) ^ (F:state_1_q___X5) - state_0_q___X5, state_1_q___X5
    SHUFFLE 7, 2, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x061 Copy 7 to 2
    STORE   7, 0xAA, 0, 0x002, INVERSE       // @ 0x062 Flushing out sum_state_q___X4, sum_state_q___X3, sum_state_q___X2, sum_state_q___X1
    TRUTH   5, 7, 0, 3, 0, 0, 0x66           // @ 0x063 TT103 - (<nx_gate_91_OR>) ^ (<nx_gate_92_XOR>) - TT4, TT50
    TRUTH   0, 3, 0, 1, 5, 0, 0x66           // @ 0x064 TT55 - (F:state_0_q___X6) ^ (F:state_1_q___X6) - state_0_q___X6, state_1_q___X6
    TRUTH   5, 7, 0, 2, 0, 0, 0x66           // @ 0x065 TT104 - (<nx_gate_98_OR>) ^ (<nx_gate_99_XOR>) - TT5, TT55
    TRUTH   0, 3, 0, 2, 6, 0, 0x66           // @ 0x066 TT61 - (F:state_0_q___X7) ^ (F:state_1_q___X7) - state_0_q___X7, state_1_q___X7
    TRUTH   5, 7, 0, 1, 0, 0, 0x66           // @ 0x067 TT105 - (<nx_gate_105_OR>) ^ (<nx_gate_106_XOR>) - TT60, TT61
    LOAD    0, 0, 0x003, PRESERVE            // @ 0x068 Loading R0 with state_1_q___X0, state_0_q___X0, -, -, -, -, -, -
    TRUTH   0, 1, 0, 1, 2, 0, 0x66           // @ 0x069 TT67 - (F:state_0_q___X0) ^ (F:state_0_q___X1) - state_0_q___X0, state_0_q___X1
    TRUTH   0, 1, 0, 0, 1, 0, 0x66           // @ 0x06A TT83 - (F:state_1_q___X0) ^ (F:state_1_q___X1) - state_1_q___X0, state_1_q___X1
    TRUTH   0, 0, 0, 1, 0, 0, 0x66           // @ 0x06B TT98 - (F:state_0_q___X0) ^ (F:state_1_q___X0) - state_0_q___X0, state_1_q___X0
    SHUFFLE 7, 1, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x06C Copy 7 to 1
    STORE   7, 0xAF, 1, 0x002, INVERSE       // @ 0x06D Flushing out sum_state_q___X0, state_1_q___X1, state_0_q___X1, sum_state_q___X7, sum_state_q___X6, sum_state_q___X5
    TRUTH   0, 0, 0, 1, 0, 0, 0x55           // @ 0x06E TT66 - !(F:state_0_q___X0) - state_0_q___X0
    TRUTH   0, 0, 0, 0, 0, 0, 0x55           // @ 0x06F TT82 - !(F:state_1_q___X0) - state_1_q___X0
flush:
    SHUFFLE 7, 0, 0, 1, 2, 3, 4, 5, 6, 7     // @ 0x070 Copy 7 to 0
    STORE   7, 0x03, 0, 0x003, INVERSE       // @ 0x071 Flushing out state_1_q___X0, state_0_q___X0
pipeline:
ports:
    LOAD    0, 0, 0x003, INVERSE             // @ 0x072
    SHUFFLE 0, 0, 1, 0, 0, 0, 0, 0, 0, 0     // @ 0x073
    STORE   0, 0x01, 0, 0x3FF, SET_LOW       // @ 0x074
    LOAD    0, 1, 0x002, INVERSE             // @ 0x075
    SHUFFLE 0, 0, 0, 2, 0, 0, 0, 0, 0, 0     // @ 0x076
    STORE   0, 0x02, 0, 0x3FF, SET_LOW       // @ 0x077
    LOAD    0, 0, 0x000, INVERSE             // @ 0x078
    SHUFFLE 0, 0, 0, 0, 5, 6, 7, 0, 0, 0     // @ 0x079
    STORE   0, 0x1C, 0, 0x3FF, SET_LOW       // @ 0x07A
    LOAD    0, 1, 0x000, INVERSE             // @ 0x07B
    SHUFFLE 0, 0, 0, 0, 0, 0, 0, 0, 1, 2     // @ 0x07C
    STORE   0, 0xE0, 0, 0x3FF, SET_LOW       // @ 0x07D
    LOAD    0, 0, 0x3FF, SET_LOW             // @ 0x07E
    SEND    0, 0, 15, 0, 0x000, PRESERVE, 0  // @ 0x07F
    LOAD    0, 1, 0x000, INVERSE             // @ 0x080
    SHUFFLE 0, 0, 3, 4, 5, 6, 7, 0, 0, 0     // @ 0x081
    STORE   0, 0x1F, 0, 0x3FF, SET_LOW       // @ 0x082
    LOAD    0, 0, 0x000, INVERSE             // @ 0x083
    SHUFFLE 0, 0, 0, 0, 0, 0, 0, 0, 1, 2     // @ 0x084
    STORE   0, 0xE0, 0, 0x3FF, SET_LOW       // @ 0x085
    LOAD    0, 0, 0x3FF, SET_LOW             // @ 0x086
    SEND    0, 0, 15, 0, 0x001, PRESERVE, 0  // @ 0x087
    LOAD    0, 0, 0x003, INVERSE             // @ 0x088
    SHUFFLE 0, 0, 0, 0, 0, 0, 0, 0, 0, 0     // @ 0x089
    STORE   0, 0x01, 0, 0x3FF, SET_LOW       // @ 0x08A
    LOAD    0, 1, 0x002, INVERSE             // @ 0x08B
    SHUFFLE 0, 0, 0, 1, 0, 0, 0, 0, 0, 0     // @ 0x08C
    STORE   0, 0x02, 0, 0x3FF, SET_LOW       // @ 0x08D
    LOAD    0, 1, 0x001, INVERSE             // @ 0x08E
    SHUFFLE 0, 0, 0, 0, 1, 2, 3, 4, 5, 6     // @ 0x08F
    STORE   0, 0xFC, 0, 0x3FF, SET_LOW       // @ 0x090
    LOAD    0, 0, 0x3FF, SET_LOW             // @ 0x091
    SEND    0, 0, 15, 0, 0x002, PRESERVE, 0  // @ 0x092
    LOAD    0, 1, 0x001, INVERSE             // @ 0x093
    SHUFFLE 0, 0, 7, 0, 0, 0, 0, 0, 0, 0     // @ 0x094
    STORE   0, 0x01, 0, 0x3FF, SET_LOW       // @ 0x095
    LOAD    0, 0, 0x001, INVERSE             // @ 0x096
    SHUFFLE 0, 0, 0, 0, 1, 2, 3, 4, 5, 6     // @ 0x097
    STORE   0, 0xFE, 0, 0x3FF, SET_LOW       // @ 0x098
    LOAD    0, 0, 0x3FF, SET_LOW             // @ 0x099
    SEND    0, 0, 15, 0, 0x003, PRESERVE, 0  // @ 0x09A
    LOAD    0, 1, 0x002, INVERSE             // @ 0x09B
    SHUFFLE 0, 0, 0, 0, 0, 0, 0, 7, 5, 3     // @ 0x09C
    STORE   0, 0xE1, 0, 0x3FF, SET_LOW       // @ 0x09D
    LOAD    0, 0, 0x002, INVERSE             // @ 0x09E
    SHUFFLE 0, 0, 0, 7, 5, 3, 1, 0, 0, 0     // @ 0x09F
    STORE   0, 0x1E, 0, 0x3FF, SET_LOW       // @ 0x0A0
    LOAD    0, 0, 0x3FF, SET_LOW             // @ 0x0A1
    SEND    0, 0, 15, 0, 0x004, PRESERVE, 0  // @ 0x0A2
msg_accum:
loop:
    BRANCH  0, 0, 0x000, INVERSE, 1, WAIT, 1 // @ 0x0A3
