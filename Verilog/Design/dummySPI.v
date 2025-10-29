module dummySPI(
    input wire        clk,
    input wire        rst,
    input wire        spi_sel,
    input wire        cs_b,
    input wire        mosi,

    output wire       clk_out,
    output reg        miso
    );
    
    reg [39:0] shift_reg_0;
    reg [39:0] shift_reg_1;
    
    always @(posedge clk or posedge rst)begin
        if(rst)begin
            shift_reg_0 <= 40'd0;
            shift_reg_1 <= 40'd0;
        end else begin
            if (cs_b == 0)begin
                if (spi_sel == 1)begin
                    shift_reg_1 <= {shift_reg_1[38:0],mosi};
                end else begin
                    shift_reg_0 <= {shift_reg_0[38:0],mosi};
                end
            end
        end
    end
    
    always @(*)begin
        if(spi_sel == 1)begin
            miso = shift_reg_1[39];
        end else begin
            miso = shift_reg_0[39];
        end
    end
    
    assign clk_out = clk;
    
endmodule
