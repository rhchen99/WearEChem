// Divide 64 MHz by 125 -> ~512 kHz
module clk_div_64m_to_512k (
    input  wire clk_in,    // 64 MHz input
    input  wire rst,       // active-high synchronous reset
    output reg  clk_out    // ~512 kHz output
);

    // 64,000,000 / 512,000 = 125
    localparam integer DIVISOR = 125;
    localparam integer CNT_WIDTH = $clog2(DIVISOR);

    reg [CNT_WIDTH-1:0] cnt;

    always @(posedge clk_in) begin
        if (rst) begin
            cnt     <= 0;
            clk_out <= 1'b0;
        end else begin
            if (cnt == DIVISOR-1) begin
                cnt     <= 0;
                clk_out <= 1'b1;   // new period starts, set high
            end else begin
                cnt <= cnt + 1'b1;
                // Simple ~50% duty: high for roughly half the count
                if (cnt < (DIVISOR/2))
                    clk_out <= 1'b1;
                else
                    clk_out <= 1'b0;
            end
        end
    end

endmodule
