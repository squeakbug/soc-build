#!/usr/bin/env python3
# polyphony_core.py

import os
from migen import *
from litex.soc.interconnect.axi import AXIInterface
from litex.soc.integration.doc import AutoDoc, ModuleDoc


class PolyphonyGraphicsCore(Module, AutoDoc):
    """Wrapper for the Polyphony 3D graphics core (pp_top).

    Interfaces:
    - Interrupt (active high)
    - AXI4 slave (control/status registers)
    - AXI4 master (memory access for vertices, textures, framebuffer)
    - Video clock input (clk_v)
    - VGA output (hsync, vsync, blank, 8-bit RGB)
    - *optional* output to HDMI controller
    """
    def __init__(self, platform, base_address,
        prefix_cores=".",
        xlen=32
    ):
        self.intro = ModuleDoc("""
        PolyphonyGraphicsCore: A hardware rasterizer for 3D graphics.

        The core uses a full AXI4 slave interface for configuration and
        a full AXI4 master interface to access main memory.
        The video output uses a separate pixel clock.
        """)

        if xlen != 32 and xlen != 64:
            raise Exception(f"xlen={xlen} is not supported")

        # Public interface
        self.interrupt = Signal()
        self.slave = AXIInterface(
            data_width=32,
            address_width=32,
            id_width=4
        )
        self.master = AXIInterface(
            data_width=32,
            address_width=32,
            id_width=4,
            aw_user_width=5,
            ar_user_width=5
        )
        self.clk_v = Signal()
        self.vga_hsync = Signal()
        self.vga_vsync = Signal()
        self.vga_blank = Signal()
        self.vga_r = Signal(8)
        self.vga_g = Signal(8)
        self.vga_b = Signal(8)

        # Add sources
        if xlen == 64:
            platform.add_verilog_include_path(f"{prefix_cores}/polyphony/rtl/include")
        if xlen == 32:
            platform.add_verilog_include_path(f"{prefix_cores}/polyphony/rtl/include_32")
        src_dirs = [
            "fm_3d", "fm_axi_m", "fm_axi_s", "fm_cmn", "fm_hdmi", "fm_hvc",
            "fm_mic", "fm_rd", "fm_sys"
        ]
        for d in src_dirs:
            platform.add_source_dir(f"{prefix_cores}/polyphony/rtl/{d}")
        platform.add_source(f"{prefix_cores}/polyphony/rtl/pp_top.v")

        # Map slave interface
        # TODO: this is bad solution: when IC master starts transaction on 0x0000xxxx addresses,
        #       then this slave (wb2axi bridge) will see wishbone active-high stb signal.
        #       IC circuit must prevent stb signal propogation to slaves by address checking with hash table.
        #
        #       В AXI или Wishbone based интерконнектах реализуют декодер, который активирует сигнал выбора
        #       (strobe) только для того ведомого, чей диапазон адресов соответствует адресу транзакции.
        #       LiteX должен создать такую логику декодирования.
        #
        #       Однако при подключении за интерконнектом, нужно "самому" беспечить,
        #       чтобы ведомый получал только те транзакции, которые попадают в его диапазон.
        self.i_araddr_s = Signal(32)
        self.i_awaddr_s = Signal(32)
        self.comb += [
            self.i_awaddr_s.eq(self.slave.aw.addr - base_address),
            self.i_araddr_s.eq(self.slave.ar.addr - base_address)
        ]

        # Instantiate the top module
        self.specials += Instance("pp_top",
            # System
            i_clk_core=ClockSignal(),
            i_rst_x=~ResetSignal(),
            o_o_int=self.interrupt,
            o_o_debug=Signal(2),

            # AXI Slave (full AXI4)
            # Write address channel
            i_i_awid_s=self.slave.aw.id,
            i_i_awaddr_s=self.i_awaddr_s,
            i_i_awlen_s=self.slave.aw.len,
            i_i_awsize_s=self.slave.aw.size,
            i_i_awburst_s=self.slave.aw.burst,
            i_i_awlock_s=self.slave.aw.lock,
            i_i_awcache_s=self.slave.aw.cache,
            i_i_awprot_s=self.slave.aw.prot,
            i_i_awvalid_s=self.slave.aw.valid,
            o_o_awready_s=self.slave.aw.ready,
            # Write data channel
            i_i_wid_s=self.slave.w.id,
            i_i_wdata_s=self.slave.w.data,
            i_i_wstrb_s=self.slave.w.strb,
            i_i_wlast_s=self.slave.w.last,
            i_i_wvalid_s=self.slave.w.valid,
            o_o_wready_s=self.slave.w.ready,
            # Write response channel
            o_o_bid_s=self.slave.b.id,
            o_o_bresp_s=self.slave.b.resp,
            o_o_bvalid_s=self.slave.b.valid,
            i_i_bready_s=self.slave.b.ready,
            # Read address channel
            i_i_arid_s=self.slave.ar.id,
            i_i_araddr_s=self.i_araddr_s,
            i_i_arlen_s=self.slave.ar.len,
            i_i_arsize_s=self.slave.ar.size,
            i_i_arburst_s=self.slave.ar.burst,
            i_i_arlock_s=self.slave.ar.lock,
            i_i_arcache_s=self.slave.ar.cache,
            i_i_arprot_s=self.slave.ar.prot,
            i_i_arvalid_s=self.slave.ar.valid,
            o_o_arready_s=self.slave.ar.ready,
            # Read data channel
            o_o_rid_s=self.slave.r.id,
            o_o_rdata_s=self.slave.r.data,
            o_o_rresp_s=self.slave.r.resp,
            o_o_rlast_s=self.slave.r.last,
            o_o_rvalid_s=self.slave.r.valid,
            i_i_rready_s=self.slave.r.ready,

            # AXI Master (full AXI4)
            # Write address channel
            o_o_awid_m=self.master.aw.id,
            o_o_awaddr_m=self.master.aw.addr,
            o_o_awlen_m=self.master.aw.len,
            o_o_awsize_m=self.master.aw.size,
            o_o_awburst_m=self.master.aw.burst,
            o_o_awlock_m=self.master.aw.lock,
            o_o_awcache_m=self.master.aw.cache,
            o_o_awuser_m=self.master.aw.user,
            o_o_awprot_m=self.master.aw.prot,
            o_o_awvalid_m=self.master.aw.valid,
            i_i_awready_m=self.master.aw.ready,
            # Write data channel
            o_o_wid_m=self.master.w.id,
            o_o_wdata_m=self.master.w.data,
            o_o_wstrb_m=self.master.w.strb,
            o_o_wlast_m=self.master.w.last,
            o_o_wvalid_m=self.master.w.valid,
            i_i_wready_m=self.master.w.ready,
            # Write response channel
            i_i_bid_m=self.master.b.id,
            i_i_bresp_m=self.master.b.resp,
            i_i_bvalid_m=self.master.b.valid,
            o_o_bready_m=self.master.b.ready,
            # Read address channel
            o_o_arid_m=self.master.ar.id,
            o_o_araddr_m=self.master.ar.addr,
            o_o_arlen_m=self.master.ar.len,
            o_o_arsize_m=self.master.ar.size,
            o_o_arburst_m=self.master.ar.burst,
            o_o_arlock_m=self.master.ar.lock,
            o_o_arcache_m=self.master.ar.cache,
            o_o_aruser_m=self.master.ar.user,
            o_o_arprot_m=self.master.ar.prot,
            o_o_arvalid_m=self.master.ar.valid,
            i_i_arready_m=self.master.ar.ready,
            # Read data channel
            i_i_rid_m=self.master.r.id,
            i_i_rdata_m=self.master.r.data,
            i_i_rresp_m=self.master.r.resp,
            i_i_rlast_m=self.master.r.last,
            i_i_rvalid_m=self.master.r.valid,
            o_o_rready_m=self.master.r.ready,

            # VGA output
            i_clk_v=self.clk_v,
            o_o_blank_x=self.vga_blank,
            o_o_hsync_x=self.vga_hsync,
            o_o_vsync_x=self.vga_vsync,
            o_o_vr=self.vga_r,
            o_o_vg=self.vga_g,
            o_o_vb=self.vga_b,
        )

