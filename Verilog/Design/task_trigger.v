module task_trigger (
    input  wire clk,                // system clock
    input  wire rst,                // system reset
    
    input  wire mode,               // 0 for adc; 1 for dac
    
    input  wire trigger_task,       // task trigger
    
    input  wire done_adc,           // adc task done flag
    input  wire done_dac,           // dac task done flag
    
    output reg  done_task,          // task done flag

    output reg  trigger_adc,        // adc trigger
    output reg  trigger_dac         // dac trigger
);

    reg [1:0] state;
    // State encoding
    localparam IDLE = 2'b00;
    localparam TRIG = 2'b01;
    localparam BUSY = 2'b10;

    reg [1:0] next_state;
    reg [31:0] cnt;

     always @(posedge clk or posedge rst) begin
        if (rst)
            state <= IDLE;
        else begin
            case (state)
                IDLE: begin
                    if (trigger_task)
                        state <= TRIG;
                    else
                        state <= IDLE;
                end

                TRIG: begin
                    // After 1 cycle, go to STATE2 regardless of mode
                    state <= BUSY;
                end

                BUSY: begin
                    if (mode == 1'b0) begin
                        if (done_adc)
                            state <= IDLE;
                        else
                            state <= BUSY;
                    end else begin
                        if (done_dac)
                            state <= IDLE;
                        else
                            state <= BUSY;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

    // Output logic
    always @(*) begin
        // Default values
        trigger_adc = 1'b0;
        trigger_dac = 1'b0;
        done_task = 1'b0;
        
        case (state)
            TRIG: begin
                if (mode == 1'b0)
                    trigger_adc = 1'b1;
                else
                    trigger_dac = 1'b1;
            end
            
            BUSY: begin
                if (mode == 1'b0 && done_adc)
                    done_task = 1'b1;   // assert done before going back to IDLE
                else if (mode == 1'b1 && done_dac)
                    done_task = 1'b1;
            end
            
            default: begin
                trigger_adc = 1'b0;
                trigger_dac = 1'b0;
            end
        endcase
    end

endmodule

