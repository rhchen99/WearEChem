module ADC_control (
    input  wire         clk,
    input  wire         rst,       // active-low reset
    input  wire         trigger,
    input  wire         mode,        // 0 = free-running, 1 = incremental mode
    input  wire [31:0]  TWAKE,           // cycles for state 1 (wake up time)
    input  wire [31:0]  TSAMPLE,           // cycles for state 3 (sample time)
    input  wire [31:0]  NSAM,           // number of samples (only used in incremental mode)
    
    output reg          done,        // ADC operation complete flag
        
    output reg          adc_out_wr,

    output reg          SLP,         // SLP signal
    output reg          DAC_STP_EXT, // DAC External startup signal
    output reg          RST_ADC,      // ADC reset signal
    
    input wire          CLK_S_D_OUT,
    input wire          ADC_OUT,
    
    output wire [31:0]  adc_data_out     
);

    // State encoding
    localparam S0 = 2'd0;
    localparam S1 = 2'd1;
    localparam S2 = 2'd2;
    localparam S3 = 2'd3;
    
    reg [1:0] state;
    
    reg [31:0] counter;
    reg [31:0] loop_count;  // counts S2↔S3 loops when mode=1
    
    wire [31:0] filter_out;
    wire [31:0] pattern;
    
    assign adc_data_out = mode ? filter_out : {31'd0,ADC_OUT};
    //assign adc_data_out = mode ? filter_out : pattern;
    
COI2_Filter adcfilter(
    .clk(CLK_S_D_OUT),
    .rst(rst),
    .rst_adc(RST_ADC),
    .din(ADC_OUT),
    .dout(filter_out)
);

adc_pattern_gen patterngen(
    .clk(CLK_S_D_OUT),
    .rst(RST_ADC),
    .data_out(pattern)
);
    
    // FSM sequential logic
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state      <= S0;
            counter    <= 32'd0;
            loop_count <= 32'd0;
            done       <= 1'b0;
                        
        end else begin
            done <= 1'b0;  // default

            case (state)
                // Reset/Idle
                S0: begin
                    counter    <= 32'd0;
                    loop_count <= 32'd0;
                    if (trigger)
                        state <= S1;
                end

                // Wait N cycles
                S1: begin
                    if (counter >= TWAKE - 1) begin
                        counter <= 32'd0;
                        state   <= S2;
                    end else begin
                        counter <= counter + 1'b1;
                    end
                end

                // One-cycle state
                S2: begin
                    counter <= 32'd0;
                    state   <= S3;
                end

                // Wait M cycles
                S3: begin
                    if (mode == 0) begin
                        if(counter >= TSAMPLE-1)begin
                            counter <= 32'd0;
                            state <= S0;
                            done <= 1'b1;
                        end else begin
                            counter <= counter +1'b1;
                        end
                    end else begin
                        if(counter >= TSAMPLE+1)begin
                            counter <= 32'd0;
                            if (loop_count < NSAM -1) begin
                                loop_count <= loop_count +1'b1;
                                state <= S2;
                            end else begin
                                loop_count <= 32'd0;
                                state <= S0;
                                done <= 1'b1;
                            end
                        end else begin
                            counter <= counter +1'b1;
                        end
                    
                    end
                end

                default: state <= S0;
            endcase
        end
    end

    // Decoder combinational logic
    always @(*) begin
        SLP         = 1'b0;
        DAC_STP_EXT = 1'b0;
        RST_ADC     = 1'b0;
        adc_out_wr = 1'b0;
        
        case (state)
            S0: begin
                SLP         = 1'b1;
                DAC_STP_EXT = 1'b0;
                RST_ADC     = 1'b1;
                adc_out_wr  = 1'b0;
            end

            S1: begin
                SLP         = 1'b0;
                DAC_STP_EXT = 1'b0;
                RST_ADC     = 1'b1;
                adc_out_wr  = 1'b0;
            end

            S2: begin
                SLP         = 1'b0;
                DAC_STP_EXT = 1'b1;
                RST_ADC     = 1'b1;
                adc_out_wr  = 1'b0;
            end

            S3: begin
                SLP         = 1'b0;
                DAC_STP_EXT = 1'b1;
                RST_ADC     = 1'b0;
                adc_out_wr  = 1'b0;
                
                if(mode == 0)begin
                    adc_out_wr  = 1'b1;        
                end else if (mode == 1 && counter == TSAMPLE +1) begin
                    adc_out_wr  = 1'b1;
                end
            end
        endcase
    end

endmodule
