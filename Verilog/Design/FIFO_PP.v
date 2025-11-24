module FIFO_PP(
    input   wire            rst,
    input   wire            rd_clk,
    input   wire            wr_clk,
    input   wire            wr_en,
    input   wire            rd_en,
    
    input   wire            force_flip,
    
    output  wire            full,
    output  wire            empty,    
    
    input   wire    [31:0]  data_in,
    output  wire    [31:0]  data_out
    );


reg sel;

wire [31:0] data_out_ping;
wire [31:0] data_out_pong;

wire almost_full_ping;
wire almost_full_pong;

//assign full = sel? full_pong : full_ping;
assign full = sel? almost_full_pong : almost_full_ping;
assign empty = sel? empty_ping : empty_pong;

assign wr_en_ping = !sel & wr_en;
assign wr_en_pong = sel & wr_en;
assign rd_en_ping = sel & rd_en;
assign rd_en_pong = !sel & rd_en;

assign flip = (sel? almost_full_pong : almost_full_ping) | force_flip;
assign data_out = sel? data_out_ping : data_out_pong;

always @(posedge wr_clk or posedge rst) begin
    if (rst) begin
        sel <= 1'b0; // start writing to ping and reading from pong
    end else begin
        if (flip)
            sel <= ~sel;
    end
end

fifo_w32_d131072 fifo_ping(
    .wr_clk(wr_clk),
    .rd_clk(rd_clk),
    .rst(rst),
    .din(data_in),
    .wr_en(wr_en_ping),
    .rd_en(rd_en_ping),
    .dout(data_out_ping),
    .full(full_ping),
    .empty(empty_ping),
    .almost_full(almost_full_ping)
);

fifo_w32_d131072 fifo_pong(
    .wr_clk(wr_clk),
    .rd_clk(rd_clk),
    .rst(rst),
    .din(data_in),
    .wr_en(wr_en_pong),
    .rd_en(rd_en_pong),
    .dout(data_out_pong),
    .full(full_pong),
    .empty(empty_pong),
    .almost_full(almost_full_pong)
);

endmodule