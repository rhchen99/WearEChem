`timescale 1ns / 100ps

module spi_tst_1(
);    

reg [39:0] data_in;

reg clk;
reg rst;
reg trigger_sys;
reg rd_en_fifo_spi_out;
wire done_spi;
wire [39:0] fifo_spi_out;

WETOP DUT(
.clk(clk),
.rst(rst),
.data_in(data_in),
.trigger_sys(trigger_sys),
.rd_en_fifo_spi_out(rd_en_fifo_spi_out),
.done_spi(done_spi),
.fifo_spi_out(fifo_spi_out)
);

always #5 clk=~clk;

initial begin
    clk = 0;
    rst = 1;
    
    rd_en_fifo_spi_out = 0;
    trigger_sys = 0;
    
    data_in = 40'h6e5f3a4d45;
    
    #10 rst = 0;
    #10 trigger_sys = 1;
    #10 trigger_sys = 0;
    #500;
    #10 trigger_sys = 1;
    #10 trigger_sys = 0;
    #500;
    rd_en_fifo_spi_out = 1;
    #500;
    $finish;
    end


endmodule
