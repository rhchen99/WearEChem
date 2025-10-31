module COI2_Filter(
    input  wire                 clk,
    input  wire                 rst,
    input  wire                 rst_adc,
    input  wire                 din,
    output reg    [31:0]        dout
);

    reg   [31:0] int1;
    reg   [31:0] int2;

    always @(posedge clk or posedge rst_adc) begin
        if (rst_adc) begin
            int1 <= 0;
            int2 <= 0;
        end else begin
            int1 <= int1 + din;
            int2 <= int2 + int1;
        end
    end

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            dout <= 0;
        end else begin
            dout <= int2;
        end
    end

endmodule
