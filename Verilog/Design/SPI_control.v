module SPI_control(
    input wire        clk,
    input wire        rst,
    
    input wire [39:0] data_in,    
    
    input wire        trigger_sys,
    input wire        trigger_dac,
    
    input wire        miso,
    
    output reg [39:0] data_out,
    
    output reg        done,
    output reg        spi_sel,
    output reg        cs_b,
    output reg        mosi,
    
    output reg        wr_en
);
    
    always @(posedge clk or posedge rst)begin
        if(rst)begin
            data_out <= 40'd0;
        end else begin
            if(!cs_b)begin
                data_out <= {data_out[38:0],miso};
            end
        end
    end
    
    reg [1:0] state;
    reg [1:0] next_state;
    
// State encoding
    localparam IDLE = 2'd0;
    localparam CONFIG = 2'd1;
    localparam DAC = 2'd2;
    
    reg [39:0]  shift_reg;
    reg [5:0]   bit_cnt;
    
    
    always @(posedge clk or posedge rst) begin
        if(rst)begin
            wr_en <= 0;
        end else begin
            wr_en <= done;
        end
    end
    
    always @(posedge clk or posedge rst) begin
        if(rst)begin
            state       <= IDLE;
            spi_sel     <= 1'b0;
            shift_reg   <= 40'd0;
            bit_cnt     <= 6'd0;
            cs_b        <= 1'b1;
            mosi        <= 1'b0;
            done        <= 1'b0;            
        end else begin
            spi_sel <= 1'b0;
            state <= next_state;
            done <= 1'b0;
            case(state)
                IDLE: begin
                    cs_b <= 1'b1;
                    if(trigger_sys) begin
                        shift_reg <= data_in;
                        bit_cnt <= 6'd39;
                    end
                    if(trigger_dac) begin
                        shift_reg <= data_in;
                        bit_cnt <= 6'd39;
                    end
                end
                CONFIG: begin
                    cs_b <= 1'b0;
                    spi_sel <= 1'b0;
                    mosi <= shift_reg[39];
                    shift_reg <= {shift_reg[38:0],1'b0};
                
                    if (bit_cnt > 0)
                        bit_cnt <= bit_cnt-1'b1;
                    else begin
                        done <= 1'b1;
                    end
                end
                DAC: begin
                    cs_b <= 1'b0;
                    spi_sel <= 1'b1;
                    mosi <= shift_reg[39];
                    shift_reg <= {shift_reg[38:0],1'b0};
                
                    if (bit_cnt > 0)
                        bit_cnt <= bit_cnt-1'b1;
                    else begin
                        done <= 1'b1;
                    end
                end
            endcase
        end
        
    end
    
    // FSM next state logic
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (trigger_sys)
                    next_state = CONFIG;
                if (trigger_dac)
                    next_state = DAC;
            end
            CONFIG: begin
                if (bit_cnt == 0)
                    next_state = IDLE;
            end
            DAC: begin
                if (bit_cnt == 0)
                    next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end
    
endmodule
