#!/usr/bin/env python3
# polyphony_core.py

import os

from migen import *
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import *
from litex.soc.integration.doc import AutoDoc, ModuleDoc

class WF3DCore(Module, AutoDoc):
    """Wrapper for the WireFrame 3D graphics core.

    Public interfaces:
    - interrupt
    - slave  --- Wishbone slave for registers access
    - master --- Wishbone master for DMA operations
    """
    def __init__(self, platform,
        prefix_cores="."
    ):
        self.intro = ModuleDoc("""
        WF3DCore: A hardware rasterizer for 3D graphics.

        The core uses a Wishbone slave interface for configuration and
        a Wishbone interface to access main memory.
        """)

        # Public interface
        self.interrupt = Signal()
        self.slave = wishbone.Interface()
        self.master = wishbone.Interface()

        # Add sources
        platform.add_verilog_include_path(
            f"{prefix_cores}/wf3d/tags/release-1.2/rtl/include"
        )
        platform.add_source_dir(
            f"{prefix_cores}/wf3d/tags/release-1.2/rtl/core"
        )

        # Instantiate top-level module
        self.specials += Instance("fm_3d_core",
            # system
            i_clk_i   = ClockSignal("sys"),
            i_rst_i   = ResetSignal("sys"),
            o_int_o   = self.interrupt,

            # WishBone Slave
            i_s_wb_adr_i  = self.slave.adr,
            o_s_wb_dat_o  = self.slave.dat_w,
            i_s_wb_dat_i  = self.slave.dat_r,
            i_s_wb_sel_i  = self.slave.sel,
            i_s_wb_stb_i  = self.slave.stb,
            o_s_wb_ack_o  = self.slave.ack,
            i_s_wb_we_i   = self.slave.we,

            # WishBone Master
            o_m_wb_adr_o  = self.master.adr,
            o_m_wb_dat_o  = self.master.dat_w,
            i_m_wb_dat_i  = self.master.dat_r,
            o_m_wb_sel_o  = self.master.sel,
            o_m_wb_stb_o  = self.master.stb,
            i_m_wb_ack_i  = self.master.ack,
            o_m_wb_we_o   = self.master.we,
       )

