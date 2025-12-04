module SPI_control(
    input wire        clk,
    input wire        rst,
    
    input wire        spi_clk_out,
    
    input wire [31:0] data_in_wav,
    input wire [31:0] data_in_config_msb,    
    input wire [31:0] data_in_config_lsb,    
    
    input wire        trigger_config,
    input wire        trigger_dac,
    
    input wire        miso,
    
    output wire       spiClk,
    
    output reg [31:0] data_out_msb,
    output reg [31:0] data_out_lsb,
    
    output reg        done,
    output reg        spi_sel,
    output reg        cs_b,
    output reg        mosi,
    
    output reg        spi_wav_rd,
    output reg        spi_config_rd,
    output reg        spi_out_wr
);
    
    assign spiClk = (~clk)&(~cs_b);
    
    always @(posedge clk or posedge rst)begin
        if(rst)begin
            data_out_msb <= 32'd0;
            data_out_lsb <= 32'd0;
        end else begin
            if(!cs_b)begin
                data_out_lsb <= {data_out_lsb[30:0],miso};
                data_out_msb <= {24'd0,data_out_msb[6:0],data_out_lsb[31]};
            end
        end
    end
    
    reg [2:0] state;
    reg [2:0] next_state;
    
// State encoding
    localparam IDLE = 3'd0;
    localparam CONFIG = 3'd1;
    localparam DAC = 3'd2;
    
    localparam LOAD_CONFIG = 3'd3;
    localparam LOAD_DAC = 3'd4;
    
    reg [39:0]  shift_reg;
    reg [5:0]   bit_cnt;
    reg cnt;
    
    always @(posedge clk or posedge rst) begin
        if(rst)begin
            spi_out_wr <= 0;
        end else begin
            spi_out_wr <= done;
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
            cnt         <= 0;
            spi_config_rd <= 0;
            spi_wav_rd <= 0;
                        
        end else begin
            spi_config_rd <= 0;
            spi_wav_rd <= 0;
            spi_sel <= 1'b0;
            state <= next_state;
            done <= 1'b0;
            case(state)
                IDLE: begin
                    cs_b <= 1'b1;
                    cnt <= 0;
                    if(trigger_config) begin
                        spi_config_rd <= 1;
                    end
                    if(trigger_dac) begin
                        spi_wav_rd <= 1;
                    end
                end
                LOAD_CONFIG: begin
                    cnt <= cnt +1;
                    if(cnt)begin
                        shift_reg <= {data_in_config_msb[7:0], data_in_config_lsb};
                        bit_cnt <= 6'd39;
                    end
                end
                LOAD_DAC: begin
                    cnt <= cnt +1;
                    if(cnt)begin
                        shift_reg <= {data_in_wav,8'b0};
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
                if (trigger_config)
                    next_state = LOAD_CONFIG;
                if (trigger_dac)
                    next_state = LOAD_DAC;
            end
            LOAD_CONFIG: begin
                if(cnt)
                next_state = CONFIG;
            end
            LOAD_DAC: begin
                if(cnt)
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
