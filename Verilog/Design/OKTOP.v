//==========================================================================
// OKTOP - FrontPanel wrapper for WETOP with dummySPI + dummyADC
//==========================================================================

module OKTOP (
    // ---- Opal Kelly Host Interface -------------------------------------
    input  wire [4:0]  okUH,
    output wire [2:0]  okHU,
    inout  wire [31:0] okUHU,
    inout  wire        okAA,

    // ---- Differential board clock  -----------
    input  wire sys_clkp,
    input  wire sys_clkn

);

    //=====================================================================
    // Board 100 MHz clock buffer 
    //=====================================================================
    wire sys_clk;
    IBUFGDS osc_clk (
        .O (sys_clk),
        .I (sys_clkp),
        .IB(sys_clkn)
    );

    //=====================================================================
    // FrontPanel host plumbing
    //=====================================================================
    wire        okClk;
    wire [112:0] okHE;
    wire [64:0]  okEH;

    wire [65*6-1:0] okEHx;

    okHost okHI (
        .okUH (okUH),
        .okHU (okHU),
        .okUHU(okUHU),
        .okAA (okAA),
        .okClk(okClk),
        .okHE (okHE),
        .okEH (okEH)
    );

    okWireOR #(.N(6)) wireOR (
        .okEH (okEH),
        .okEHx(okEHx)
    );

    //=====================================================================
    // WireIns: reset, modes, DAC + ADC settings
    //=====================================================================
    wire [31:0] wi00, wi01, wi02, wi03, wi04, wi05, wi06, wi07, wi08;

    okWireIn w00 (.okHE(okHE), .ep_addr(8'h00), .ep_dataout(wi00));
    okWireIn w01 (.okHE(okHE), .ep_addr(8'h01), .ep_dataout(wi01));
    okWireIn w02 (.okHE(okHE), .ep_addr(8'h02), .ep_dataout(wi02));
    okWireIn w03 (.okHE(okHE), .ep_addr(8'h03), .ep_dataout(wi03));
    okWireIn w04 (.okHE(okHE), .ep_addr(8'h04), .ep_dataout(wi04));
    okWireIn w05 (.okHE(okHE), .ep_addr(8'h05), .ep_dataout(wi05));
    okWireIn w06 (.okHE(okHE), .ep_addr(8'h06), .ep_dataout(wi06));
    okWireIn w07 (.okHE(okHE), .ep_addr(8'h07), .ep_dataout(wi07));
    okWireIn w08 (.okHE(okHE), .ep_addr(8'h08), .ep_dataout(wi08));

    // ASIC config wires
    wire [31:0] wi09, wi0A, wi0B, wi0C, wi0D, wi0E;

    okWireIn w09 (.okHE(okHE), .ep_addr(8'h09), .ep_dataout(wi09)); // PSTAT enables
    okWireIn w0A (.okHE(okHE), .ep_addr(8'h0A), .ep_dataout(wi0A)); // I2X switches
    okWireIn w0B (.okHE(okHE), .ep_addr(8'h0B), .ep_dataout(wi0B)); // CC gain/sel
    okWireIn w0C (.okHE(okHE), .ep_addr(8'h0C), .ep_dataout(wi0C)); // ADC OTA1/2
    okWireIn w0D (.okHE(okHE), .ep_addr(8'h0D), .ep_dataout(wi0D)); // ADC startup/c2
    okWireIn w0E (.okHE(okHE), .ep_addr(8'h0E), .ep_dataout(wi0E)); // CGM_EXT

    // Decode control & settings
    wire rst_we    = wi00[0];
    wire task_mode = wi00[1];
    wire dac_mode  = wi00[2];
    wire adc_mode  = wi00[3];

    wire [31:0] dac_T1   = wi01;
    wire [31:0] dac_T2   = wi02;
    wire [31:0] dac_TS1  = wi03;
    wire [31:0] dac_TS2  = wi04;
    wire [31:0] dac_NSAM = wi05;

    wire [31:0] adc_TWAKE   = wi06;
    wire [31:0] adc_TSAMPLE = wi07;
    wire [31:0] adc_NSAM    = wi08;

    //=====================================================================
    // TriggerIn
    //=====================================================================
    wire [31:0] trig40;
    okTriggerIn t40 (
        .okHE      (okHE),
        .ep_addr   (8'h40),
        .ep_clk    (okClk),
        .ep_trigger(trig40)
    );

    wire trigger_config = trig40[0];
    wire trigger_task   = trig40[1];

    //=====================================================================
    // PipeIn 0x80 : Config FIFO
    //=====================================================================
    wire [31:0] cfg_pipe_data;
    wire        cfg_pipe_write;

    okPipeIn p80_cfg (
        .okHE(okHE),
        .okEH(okEHx[3*65 +: 65]),
        .ep_addr(8'h80),
        .ep_dataout(cfg_pipe_data),
        .ep_write(cfg_pipe_write)
    );

    reg [31:0] cfg_msb_reg, cfg_lsb_reg;
    reg        cfg_phase;
    reg        spi_config_wr_reg;

    always @(posedge okClk or posedge rst_we) begin
        if (rst_we) begin
            cfg_msb_reg       <= 32'd0;
            cfg_lsb_reg       <= 32'd0;
            cfg_phase         <= 1'b0;
            spi_config_wr_reg <= 1'b0;
        end else begin
            spi_config_wr_reg <= 1'b0;
            if (cfg_pipe_write) begin
                if (!cfg_phase) begin
                    cfg_msb_reg <= cfg_pipe_data;
                    cfg_phase   <= 1'b1;
                end else begin
                    cfg_lsb_reg       <= cfg_pipe_data;
                    cfg_phase         <= 1'b0;
                    spi_config_wr_reg <= 1'b1;
                end
            end
        end
    end

    wire [31:0] spi_config_msb_host = cfg_msb_reg;
    wire [31:0] spi_config_lsb_host = cfg_lsb_reg;
    wire        spi_config_wr       = spi_config_wr_reg;

    // ASIC config packer (40-bit)
    wire [39:0] asic_word = {
        wi0C[4:0],      // ADC OTA settings
        wi0D[2:0],      // ADC startup sel
        wi0D[7:4],      // ADC C2
        wi09[6:0],      // PSTAT block enables
        wi0A[3:0],      // I2X switches
        wi0B[2:0],      // CC gain
        wi0B[11:7],     // CC sel (5 bits)
        wi0E[0],        // CGM_EXT
        8'd0            // pad
    };

    // Select host 40-bit or ASIC 40-bit
    wire use_host = spi_config_wr;
    wire [39:0] spi_word = use_host ?
                           {spi_config_msb_host[7:0], spi_config_lsb_host} :
                           asic_word;

    // Split into MSB/LSB for SPI_control
    wire [31:0] spi_config_msb_in = {24'd0, spi_word[39:32]};
    wire [31:0] spi_config_lsb_in = spi_word[31:0];

    //=====================================================================
    // PipeIn 0x81 : waveform
    //=====================================================================
    wire [31:0] spi_wav_in;
    wire        spi_wav_wr;

    okPipeIn p81_wav (
        .okHE(okHE),
        .okEH(okEHx[4*65 +: 65]),
        .ep_addr(8'h81),
        .ep_dataout(spi_wav_in),
        .ep_write(spi_wav_wr)
    );

    //=====================================================================
    // WireOut 0x20
    //=====================================================================
    wire [31:0] status20;

    okWireOut w20 (
        .okHE(okHE),
        .okEH(okEHx[0 +: 65]),
        .ep_addr(8'h20),
        .ep_datain(status20)
    );

    //=====================================================================
    // PipeOut SPI
    //=====================================================================
    wire [31:0] data_out_spi_msb;
    wire [31:0] data_out_spi_lsb;
    wire        spi_out_rd;

    okPipeOut pA0_spi (
        .okHE(okHE),
        .okEH(okEHx[1*65 +: 65]),
        .ep_addr(8'hA0),
        .ep_datain(data_out_spi_msb),
        .ep_read(spi_out_rd)
    );

    //=====================================================================
    // PipeOut ADC
    //=====================================================================
    wire [31:0] data_out_adc;
    wire        adc_out_rd;

    okPipeOut pA1_adc (
        .okHE(okHE),
        .okEH(okEHx[2*65 +: 65]),
        .ep_addr(8'hA1),
        .ep_datain(data_out_adc),
        .ep_read(adc_out_rd)
    );

    //=====================================================================
    // TriggerOut 0x60
    //=====================================================================
    wire done_spi, done_task;

    reg done_task_q;
    always @(posedge okClk or posedge rst_we) begin
        if (rst_we)
            done_task_q <= 1'b0;
        else
            done_task_q <= done_task;
    end

    wire task_done_pulse = done_task & ~done_task_q;

    wire [31:0] trig60_bus;
    assign trig60_bus[0] = task_done_pulse;

    okTriggerOut t60 (
        .okHE(okHE),
        .okEH(okEHx[5*65 +: 65]),
        .ep_addr(8'h60),
        .ep_clk(okClk),
        .ep_trigger(trig60_bus)
    );

    //=====================================================================
    // Dummy SPI + ADC wiring
    //=====================================================================
    wire MOSI, MISO, CS_B, SPI_SEL, DACSYNC;
    wire SPI_CLK_OUT;
    wire CLK_S_D_OUT, ADC_OUT;
    wire RST_ADC, DAC_STP_EXT, SLP;

    //=====================================================================
    // WETOP instance
    //=====================================================================
    WETOP wetop_inst (
        .clk(okClk),
        .rst(rst_we),

        .task_mode(task_mode),
        .dac_mode(dac_mode),
        .dac_T1(dac_T1),
        .dac_T2(dac_T2),
        .dac_TS1(dac_TS1),
        .dac_TS2(dac_TS2),
        .dac_NSAM(dac_NSAM),

        .adc_mode(adc_mode),
        .adc_TWAKE(adc_TWAKE),
        .adc_TSAMPLE(adc_TSAMPLE),
        .adc_NSAM(adc_NSAM),

        .trigger_config(trigger_config),
        .trigger_task(trigger_task),

        .adc_out_rd(adc_out_rd),
        .spi_out_rd(spi_out_rd),
        .spi_wav_wr(spi_wav_wr),
        .spi_config_wr(spi_config_wr),

        .done_spi(done_spi),
        .done_task(done_task),

        .spi_config_msb_in(spi_config_msb_in),
        .spi_config_lsb_in(spi_config_lsb_in),
        .spi_wav_in(spi_wav_in),

        .data_out_spi_msb(data_out_spi_msb),
        .data_out_spi_lsb(data_out_spi_lsb),
        .data_out_adc(data_out_adc),

        .MISO(MISO),
        .SPI_CLK_OUT(SPI_CLK_OUT),
        .CLK_S_D_OUT(CLK_S_D_OUT),
        .ADC_OUT(ADC_OUT),

        .MOSI(MOSI),
        .CS_B(CS_B),
        .SPI_SEL(SPI_SEL),
        .DACSYNC(DACSYNC),

        .RST_ADC(RST_ADC),
        .DAC_STP_EXT(DAC_STP_EXT),
        .SLP(SLP)
    );

    dummySPI fake_spi (
        .clk(okClk),
        .rst(rst_we),
        .spi_sel(SPI_SEL),
        .cs_b(CS_B),
        .mosi(MOSI),
        .clk_out(SPI_CLK_OUT),
        .miso(MISO)
    );

    dummyADC fake_adc (
        .clk(okClk),
        .rst_adc(RST_ADC),
        .slp(SLP),
        .clk_s_d_out(CLK_S_D_OUT),
        .dout(ADC_OUT)
    );

    assign status20[0]    = done_spi;
    assign status20[1]    = done_task;
    assign status20[31:2] = 30'd0;

endmodule
