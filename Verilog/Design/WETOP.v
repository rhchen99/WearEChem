module WETOP(
    input   wire            clk,                //system clock (should be 512kHz)
    input   wire            rst,                //system reset
    //task settings
    input   wire            task_mode,
    //dac settings
    input   wire   [1:0]    dac_mode,
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
    input   wire            adc_out_rd,    //adc output fifo read enable
    input   wire            spi_out_rd,    //spi output fifo read enable
    input   wire            spi_wav_wr,
    input   wire            spi_config_wr,
    

    output  wire            done_spi,           //spi FSM done flag
    output  wire            done_task,          //task done flag
    
    //data input
    input   wire    [31:0]  spi_config_msb_in,
    input   wire    [31:0]  spi_config_lsb_in,      
    input   wire    [31:0]  spi_wav_in,
    //data output
    output  wire    [31:0]  data_out_spi_msb,       //spi output fifo data output
    output  wire    [31:0]  data_out_spi_lsb,       //spi output fifo data output
    output  wire    [31:0]  data_out_adc,           //spi output fifo data output
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
wire [31:0] data_in_config_msb;
wire [31:0] data_in_config_lsb;
wire [31:0] adc_data_out;

assign trigger_adc = trigger_adc_task || trigger_adc_dac;

task_trigger task_trigger(
    .clk(clk),
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
    .clk(clk),
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
    .clk(clk),
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
    .clk(clk),
    .rst(rst),
    
    .data_in_wav(data_in_wav),
    .data_in_config_msb(data_in_config_msb),
    .data_in_config_lsb(data_in_config_lsb),
    
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


fifo_sync #(
    .DATA_WIDTH(32),
    .DEPTH(1024)
) wav_fifo (
    .clk     (clk),
    .rst     (rst),

    .wr_en   (spi_wav_wr),
    .wr_data (spi_wav_in),

    .rd_en   (spi_wav_rd),
    .rd_data (data_in_wav)

);

fifo_sync #(
    .DATA_WIDTH(32),
    .DEPTH(4)
) config_msb_fifo (
    .clk     (clk),
    .rst     (rst),

    .wr_en   (spi_config_wr),
    .wr_data (spi_config_msb_in),

    .rd_en   (spi_config_rd),
    .rd_data (data_in_config_msb)

);

fifo_sync #(
    .DATA_WIDTH(32),
    .DEPTH(4)
) config_lsb_fifo (
    .clk     (clk),
    .rst     (rst),

    .wr_en   (spi_config_wr),
    .wr_data (spi_config_lsb_in),

    .rd_en   (spi_config_rd),
    .rd_data (data_in_config_lsb)

);

fifo_sync #(
    .DATA_WIDTH(32),
    .DEPTH(1024)
) spi_out_msb_fifo (
    .clk     (clk),
    .rst     (rst),

    .wr_en   (spi_out_wr),
    .wr_data (spi_out_msb),

    .rd_en   (spi_out_rd),
    .rd_data (data_out_spi_msb)
);

fifo_sync #(
    .DATA_WIDTH(32),
    .DEPTH(1024)
) spi_out_lsb_fifo (
    .clk     (clk),
    .rst     (rst),

    .wr_en   (spi_out_wr),
    .wr_data (spi_out_lsb),

    .rd_en   (spi_out_rd),
    .rd_data (data_out_spi_lsb)
);


fifo_sync #(
    .DATA_WIDTH(32),
    .DEPTH(1024)
) adc_out_fifo (
    .clk     (clk),
    .rst     (rst),

    .wr_en   (adc_out_wr),
    .wr_data (adc_data_out),

    .rd_en   (adc_out_rd),
    .rd_data (data_out_adc)
);


endmodule
