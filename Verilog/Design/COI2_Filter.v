module COI2_Filter(
    input  wire                 clk,
    input  wire                 rst,
    input  wire                 din,
    output reg    [31:0]        dout
);

    reg   [31:0] int1;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            int1 <= 0;
            dout <= 0;
        end else begin
            int1 <= int1 + din;
            dout <= dout + int1;
        end
    end
    
endmodule
