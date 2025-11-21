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

    wire [65*10-1:0] okEHx;

    okHost okHI (
        .okUH (okUH),
        .okHU (okHU),
        .okUHU(okUHU),
        .okAA (okAA),
        .okClk(okClk),
        .okHE (okHE),
        .okEH (okEH)
    );

    okWireOR #(.N(10)) wireOR (
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
    
    //==============
    //clock
    //==============
    wire weClk;
    
//    clk_wiz_0 clk_64m(
//        .clk_sys(sys_clk),
//        .clk_64m(weClk),
//        .reset(rst_we)
//    );
    assign weClk = okClk;

    //=====================================================================
    // TriggerIn
    //=====================================================================
    wire [31:0] trig40;
    okTriggerIn t40 (
        .okHE      (okHE),
        .ep_addr   (8'h40),
        .ep_clk    (weClk),
        .ep_trigger(trig40)
    );

    wire trigger_config = trig40[0];
    wire trigger_task   = trig40[1];

    //=====================================================================
    // PipeIn 0x80 : spi_msb
    //=====================================================================
    wire [31:0] spi_config_msb_in;
    wire        spi_config_msb_wr;

    okPipeIn p80_spi_msb (
        .okHE(okHE),
        .okEH(okEHx[0*65 +: 65]),
        .ep_addr(8'h80),
        .ep_dataout(spi_config_msb_in),
        .ep_write(spi_config_msb_wr)
    );
    
    //=====================================================================
    // PipeIn 0x81 : spi_lsb
    //=====================================================================
    wire [31:0] spi_config_lsb_in;
    wire        spi_config_lsb_wr;

    okPipeIn p81_spi_lsb (
        .okHE(okHE),
        .okEH(okEHx[1*65 +: 65]),
        .ep_addr(8'h81),
        .ep_dataout(spi_config_lsb_in),
        .ep_write(spi_config_lsb_wr)
    );
    
    //=====================================================================
    // PipeIn 0x82 : waveform
    //=====================================================================
    wire [31:0] spi_wav_in;
    wire        spi_wav_wr;

    okPipeIn p82_wav (
        .okHE(okHE),
        .okEH(okEHx[2*65 +: 65]),
        .ep_addr(8'h82),
        .ep_dataout(spi_wav_in),
        .ep_write(spi_wav_wr)
    );
    
    //=====================================================================
    // WireOut 0x20
    //=====================================================================
    wire [31:0] status20;

    okWireOut w20 (
        .okHE(okHE),
        .okEH(okEHx[3*65 +: 65]),
        .ep_addr(8'h20),
        .ep_datain(status20)
    );
    
    //=====================================================================
    // WireOut 0x21 spi_done_count
    //=====================================================================
    wire [31:0] status21;

    okWireOut w21 (
        .okHE(okHE),
        .okEH(okEHx[8*65 +: 65]),
        .ep_addr(8'h21),
        .ep_datain(status21)
    );
    
    wire [31:0] status22;

    okWireOut w22 (
        .okHE(okHE),
        .okEH(okEHx[9*65 +: 65]),
        .ep_addr(8'h22),
        .ep_datain(status22)
    );

    //=====================================================================
    // PipeOut 0xA0: spi_msb
    //=====================================================================
    wire [31:0] data_out_spi_msb;
    wire        spi_out_msb_rd;

    okPipeOut pA0_spi_msb (
        .okHE(okHE),
        .okEH(okEHx[4*65 +: 65]),
        .ep_addr(8'hA0),
        .ep_datain(data_out_spi_msb),
        .ep_read(spi_out_msb_rd)
    );
    
    //=====================================================================
    // PipeOut 0xA1: spi_lsb
    //=====================================================================
    wire [31:0] data_out_spi_lsb;
    wire        spi_out_lsb_rd;

    okPipeOut pA1_spi_lsb (
        .okHE(okHE),
        .okEH(okEHx[5*65 +: 65]),
        .ep_addr(8'hA1),
        .ep_datain(data_out_spi_lsb),
        .ep_read(spi_out_lsb_rd)
    );

    //=====================================================================
    // PipeOut 0xA2: adc
    //=====================================================================
    wire [31:0] data_out_adc;
    wire        adc_out_rd;

    okPipeOut pA2_adc (
        .okHE(okHE),
        .okEH(okEHx[6*65 +: 65]),
        .ep_addr(8'hA2),
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
        .okEH(okEHx[7*65 +: 65]),
        .ep_addr(8'h60),
        .ep_clk(weClk),
        .ep_trigger(trig60_bus)
    );
    
    reg [31:0] spi_done_cnt;
    always @(posedge okClk or posedge rst_we) begin
        if (rst_we)
            spi_done_cnt <= 32'd0;
        else if (done_spi)begin
            spi_done_cnt <= spi_done_cnt + 1;
        end
    end
    
    reg [31:0] task_done_cnt;
    always @(posedge okClk or posedge rst_we) begin
        if (rst_we)
            task_done_cnt <= 32'd0;
        else if (done_task)begin
            task_done_cnt <= task_done_cnt + 1;
        end
    end
    

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
        .clk_100m(okClk),
        .clk_512k(weClk),
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
        .spi_out_msb_rd(spi_out_msb_rd),
        .spi_out_lsb_rd(spi_out_lsb_rd),
        
        .spi_wav_wr(spi_wav_wr),
        .spi_config_msb_wr(spi_config_msb_wr),
        .spi_config_lsb_wr(spi_config_lsb_wr),

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
        .clk(weClk),
        .rst(rst_we),
        .spi_sel(SPI_SEL),
        .cs_b(CS_B),
        .mosi(MOSI),
        .clk_out(SPI_CLK_OUT),
        .miso(MISO)
    );

    dummyADC fake_adc (
        .clk(weClk),
        .rst_adc(RST_ADC),
        .slp(SLP),
        .clk_s_d_out(CLK_S_D_OUT),
        .dout(ADC_OUT)
    );

    assign status20[0]    = done_spi;
    assign status20[1]    = done_task;
    assign status20[31:2] = 30'd0;
    assign status21       = spi_done_cnt;
    assign status22       = task_done_cnt;

endmodule
