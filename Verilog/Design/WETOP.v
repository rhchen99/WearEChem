//-----------------------------------------------------------------------------
//This module is a test module. It only consists of a SPI block
//-----------------------------------------------------------------------------
module WETOP(
    input   wire            clk,                //system clock (should be 512kHz)
    input   wire            rst,                //system reset
    input   wire    [39:0]  data_in,            //input data
    input   wire            trigger_sys,        //trigger to initiate SPI FSM
    
    input   wire            rd_en_fifo_spi_out, //spi output fifo read enable
    
    output  wire            done_spi,           //spi FSM done flag
    output  wire    [39:0]  fifo_spi_out        //spi output fifo data output

    );
    
wire miso;
wire mosi;
wire cs_b;
wire spi_sel;
wire spi_clk_out;

wire [39:0] spi_out;

wire wr_en_fifo_spi_out;

reg trigger_dac = 0;

wire full_fifo_spi_out;
wire empty_fifo_spi_out;

SPI_control spicontrol(
    .clk(clk),
    .rst(rst),
    .data_in(data_in),
    .trigger_sys(trigger_sys),
    .trigger_dac(trigger_dac),
    .miso(miso),
    .data_out(spi_out),
    .done(done_spi),
    .spi_sel(spi_sel),
    .cs_b(cs_b),
    .mosi(mosi),
    
    .wr_en(wr_en_fifo_spi_out)
);

dummySPI chipspi(
    .clk(clk),
    .rst(rst),
    .spi_sel(spi_sel),
    .cs_b(cs_b),
    .mosi(mosi),
    .clk_out(spi_clk_out),
    .miso(miso)
);

fifo_sync #(
    .DATA_WIDTH(40),
    .DEPTH(64)
) spi_output_fifo (
    .clk     (spi_clk_out),
    .rst     (rst),

    .wr_en   (wr_en_fifo_spi_out),
    .wr_data (spi_out),

    .rd_en   (rd_en_fifo_spi_out),
    .rd_data (fifo_spi_out),
    
    .full    (full_fifo_spi_out),
    .empty   (empty_fifo_spi_out)
);

endmodule
