module DAC_control(
    input  wire clk,
    input  wire rst,          // Active-low reset
    
    //settings
    input  wire [1:0]  mode,         //0: Default mode, 1: DPV mode
    input  wire [31:0] T1,    //T1 cycles
    input  wire [31:0] T2,    //T2 cycles (only for DPV)
    input  wire [31:0] TS1,
    input  wire [31:0] TS2,
    input  wire [31:0] NSAM,     //Number of cycles
        
    input  wire trigger,      // Start signal
    
    input  wire spi_done,
        
    
    output reg  adc_trigger,
    output reg  spi_trigger,
    
    output reg  done,         // Done pulse
    
    output reg  dac_sync,
    output reg  [31:0]  dac_ptr
);
    
    reg  [1:0] state;  // Current state for dac control FSM
    reg  [1:0] state1; // current state for dacsync FSM
    
    reg [31:0] cntA;   // internal counter to count time in each dac update
    
    // States (covers both modes)
    localparam IDLE   = 2'd0;
    localparam STATE1 = 2'd1; // ACTIVE for mode 0; phase 1 for mode 1
    localparam STATE2 = 2'd2; // Only used in mode 1

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            
            state <= IDLE;
            cntA  <= 0;
            dac_ptr  <= 0;
            done  <= 0;
            spi_trigger <= 0;
            adc_trigger <= 0;
        
        end else begin
            
            done <= 1'b0; // default deassert
            
            spi_trigger <= 1'b0;
            adc_trigger <= 1'b0;
            
            case (state)
                //--------------------------------------------------
                // IDLE: wait for trigger
                //--------------------------------------------------
                IDLE: begin
                    cntA <= 0;
                    dac_ptr <= 0;
                    if (trigger)
                        state <= STATE1;
                end

                //--------------------------------------------------
                // STATE1 behavior
                //--------------------------------------------------
                STATE1: begin
                    cntA <= cntA + 1'b1;
                    
                    if (cntA == TS1 && mode[1]) begin
                        adc_trigger <= 1'b1;
                    end
                    
                    if (cntA == 0) begin
                        spi_trigger <= 1'b1;
                    end
                    
                    if (mode[0] == 0) begin
                        // MODE 0 (original)
                        if (cntA == T1 - 1) begin
                            cntA <= 0;
                            dac_ptr <= dac_ptr + 1'b1;
                            if (dac_ptr == NSAM - 1) begin
                                dac_ptr <= 0;
                                done  <= 1'b1;
                                state <= IDLE;
                            end
                        end
                    end 
                    
                    else begin
                        // MODE 1 (three-state)
                        if (cntA == T1 - 1) begin
                            cntA <= 0;
                            dac_ptr <= dac_ptr + 1'b1; // increment in STATE1
                            if (dac_ptr == NSAM - 1) begin
                                dac_ptr <= 0;
                                done  <= 1'b1;
                                state <= IDLE;
                            end else begin
                                state <= STATE2;
                            end
                        end
                    end
                end

                //--------------------------------------------------
                // STATE2 (only used in mode 1)
                //--------------------------------------------------
                STATE2: begin
                    cntA <= cntA + 1'b1;
                    
                    if (cntA == 0) begin
                        spi_trigger <= 1'b1;
                    end
                    
                    if (cntA == TS2 && mode[1]) begin
                        adc_trigger <= 1'b1;
                    end
                    
                    if (cntA == T2 - 1) begin
                        cntA <= 0;
                        dac_ptr <= dac_ptr + 1'b1; // increment in STATE2
                        if (dac_ptr == NSAM - 1) begin
                            dac_ptr <= 0;
                            done  <= 1'b1;
                            state <= IDLE;
                        end else begin
                            state <= STATE1;
                        end
                    end
                end

                //--------------------------------------------------
                default: state <= IDLE;
            endcase
        end
    end

    //-------------------------------------------------
    //DAC Synchronization signal generation
    //-------------------------------------------------  
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state1     <= IDLE;
            dac_sync <= 1'b0;
        end else begin
            // Default outputs
            dac_sync <= 1'b0;
            case (state1)
                //----------------------------------------------
                // IDLE: Wait for trigger and other_state = 2 or 3
                //----------------------------------------------
                IDLE: begin
                    if (spi_done && (state == 2'd1 || state == 2'd2)) begin
                        state1     <= STATE1;
                        dac_sync <= 1'b1;  // Pulse asserted for this cycle
                    end
                end

                //----------------------------------------------
                // PULSE: one-cycle active, then return to idle
                //----------------------------------------------
                STATE1: begin
                    state1     <= IDLE;
                    dac_sync <= 1'b0;
                end

                default: state1 <= IDLE;
            endcase
        end
    end

endmodule

