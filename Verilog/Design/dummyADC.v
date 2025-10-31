module dummyADC(
    input wire clk,
    input wire rst_adc,
    input wire slp,
    output wire clk_s_d_out,
    output wire dout
    );
    
    assign clk_s_d_out = slp ? 0:clk;
    
    reg [7:0] sr;

    always @(posedge clk_s_d_out or posedge rst_adc) begin
        if (rst_adc) begin
            sr <= 8'b01010101;
        end else begin
            sr <= {sr[6:0],sr[7]};
        end
    end
    
    assign dout = sr[7];

endmodule
