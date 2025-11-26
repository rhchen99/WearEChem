module WETOP(
    input   wire            clk_100m,              //interface clock (should be 100MHz)
    
    input   wire            clk_512k,            // logic clock (should be 512kHz)
    
    input   wire            rst,                //system reset
    //task settings
    input   wire            task_mode,
    //dac settings
    input   wire            dac_mode,
    input   wire   [31:0]   dac_T1,
    input   wire   [31:0]   dac_T2,
    input   wire   [31:0]   dac_TS1,
    input   wire   [31:0]   dac_TS2,
    input   wire   [31:0]   dac_NSAM,         
    //adc settings
    input   wire            adc_mode,
    input   wire   [31:0]   adc_TWAKE,
    input   wire   [31:0]   adc_TSAMPLE,
    input   wire   [31:0]   adc_NSAM,   

    //Input triggers
    input   wire            trigger_config,     //trigger to initiate SPI FSM
    input   wire            trigger_task,       //trigger to task FSM

    //fifo read and write

    input   wire            adc_out_rd,
    
    input   wire            spi_out_msb_rd,    //spi output fifo read enable
    input   wire            spi_out_lsb_rd,    //spi output fifo read enable

    input   wire            spi_wav_wr,
    input   wire            spi_config_msb_wr,
    input   wire            spi_config_lsb_wr,
    
    output  wire            done_spi,           //spi FSM done flag
    output  wire            done_task,          //task done flag
    
    //data input
    input   wire    [31:0]  spi_config_msb_in,
    input   wire    [31:0]  spi_config_lsb_in,      
    input   wire    [31:0]  spi_wav_in,
    //data output
    output  wire    [31:0]  data_out_spi_msb,       //spi output fifo data output
    output  wire    [31:0]  data_out_spi_lsb,       //spi output fifo data output

    output  wire    [31:0]  data_out_adc,
    
    
    input   wire            force_flip,
    output  wire            full_ppfifo,
    //CHIP interface
    
    input   wire MISO,
    input   wire SPI_CLK_OUT,
    input   wire CLK_S_D_OUT,
    input   wire ADC_OUT,
    
    output  wire MOSI,
    output  wire CS_B,
    output  wire SPI_SEL,
    output  wire DACSYNC,
    
    output  wire RST_ADC,
    output  wire DAC_STP_EXT,
    output  wire SLP
);

wire [31:0] spi_out_msb;
wire [31:0] spi_out_lsb;
wire [31:0] data_in_wav;
//wire [31:0] data_in_config_msb;
//wire [31:0] data_in_config_lsb;
wire [31:0] adc_data_out;

assign trigger_adc = trigger_adc_task || trigger_adc_dac;

task_trigger task_trigger(
    .clk(clk_512k),
    .rst(rst),
    .mode(task_mode),
    .trigger_task(trigger_task),
    .done_adc(done_adc),
    .done_dac(done_dac),
    .done_task(done_task),
    .trigger_adc(trigger_adc_task),
    .trigger_dac(trigger_dac)
);

DAC_control dac_control(
    .clk(clk_512k),
    .rst(rst),
    
    .mode(dac_mode),
    .T1(dac_T1),
    .T2(dac_T2),
    .TS1(dac_TS1),
    .TS2(dac_TS2),
    .NSAM(dac_NSAM),
    
    .trigger(trigger_dac),
    
    .spi_done(done_spi),
    .adc_trigger(trigger_adc_dac),
    .spi_trigger(trigger_spi_dac),
    .done(done_dac),
    .dac_sync(DACSYNC)
);

ADC_control adc_control(
    .clk(clk_512k),
    .rst(rst),
    
    .mode(adc_mode),
    .TWAKE(adc_TWAKE),
    .TSAMPLE(adc_TSAMPLE),
    .NSAM(adc_NSAM),
    
    .trigger(trigger_adc),
    .adc_out_wr(adc_out_wr),
    
    .done(done_adc),
    .SLP(SLP),
    .DAC_STP_EXT(DAC_STP_EXT),
    .RST_ADC(RST_ADC),
    .CLK_S_D_OUT(CLK_S_D_OUT),
    .ADC_OUT(ADC_OUT),
    .adc_data_out(adc_data_out)
);



SPI_control spicontrol(
    .clk(clk_512k),
    .rst(rst),
    
    .data_in_wav(data_in_wav),
    .data_in_config_msb(spi_config_msb_in),
    .data_in_config_lsb(spi_config_lsb_in),
    
    .trigger_config(trigger_config),
    .trigger_dac(trigger_spi_dac),
    
    .miso(MISO),
    
    .data_out_msb(spi_out_msb),
    .data_out_lsb(spi_out_lsb),
    
    .done(done_spi),
    .spi_sel(SPI_SEL),
    .cs_b(CS_B),
    .mosi(MOSI),
    
    .spi_wav_rd(spi_wav_rd),
    .spi_config_rd(spi_config_rd),
    .spi_out_wr(spi_out_wr)
);


fifo_w32_d1024 wav_fifo(
    .rst(rst),
    .wr_clk(clk_100m),
    .rd_clk(clk_512k),
    .din(spi_wav_in),
    .wr_en(spi_wav_wr),
    .rd_en(spi_wav_rd),
    .dout(data_in_wav),
    .full(),
    .empty(),
    .wr_rst_busy(),
    .rd_rst_busy()
);

//fifo_w32_d1024 config_msb_fifo(
//    .rst(rst),
//    .wr_clk(clk_100m),
//    .rd_clk(clk_512k),
//    .din(spi_config_msb_in),
//    .wr_en(spi_config_msb_wr),
//    .rd_en(spi_config_rd),
//    .dout(data_in_config_msb),
//    .full(),
//    .empty(),
//    .wr_rst_busy(),
//    .rd_rst_busy()
//);

//fifo_w32_d1024 config_lsb_fifo(
//    .rst(rst),
//    .wr_clk(clk_100m),
//    .rd_clk(clk_512k),
//    .din(spi_config_lsb_in),
//    .wr_en(spi_config_lsb_wr),
//    .rd_en(spi_config_rd),
//    .dout(data_in_config_lsb),
//    .full(),
//    .empty(),
//    .wr_rst_busy(),
//    .rd_rst_busy()
//);

fifo_w32_d1024 spi_out_msb_fifo(
    .rst(rst),
    .wr_clk(clk_512k),
    .rd_clk(clk_100m),
    .din(spi_out_msb),
    .wr_en(spi_out_wr),
    .rd_en(spi_out_msb_rd),
    .dout(data_out_spi_msb),
    .full(),
    .empty(),
    .wr_rst_busy(),
    .rd_rst_busy()
);

fifo_w32_d1024 spi_out_lsb_fifo(
    .rst(rst),
    .wr_clk(clk_512k),
    .rd_clk(clk_100m),
    .din(spi_out_lsb),
    .wr_en(spi_out_wr),
    .rd_en(spi_out_lsb_rd),
    .dout(data_out_spi_lsb),
    .full(),
    .empty(),
    .wr_rst_busy(),
    .rd_rst_busy()
);

//fifo_w32_d1024 adc_out_fifo(
//    .rst(rst),
//    .wr_clk(clk_512k),
//    .rd_clk(clk_100m),
//    .din(adc_data_out),
//    .wr_en(adc_out_wr),
//    .rd_en(adc_out_rd),
//    .dout(data_out_adc),
//    .full(),
//    .empty(),
//    .wr_rst_busy(),
//    .rd_rst_busy()
//);

FIFO_PP adc_out_fifo(
    .rst(rst),
    .rd_clk(clk_100m),
    .wr_clk(clk_512k),
    .wr_en(adc_out_wr),
    .rd_en(adc_out_rd),
    .force_flip(force_flip),
    
    .full(full_ppfifo),
    .empty(),
    
    .data_in(adc_data_out),
    .data_out(data_out_adc)
);

endmodule
