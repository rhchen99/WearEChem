module fifo_sync #(
    parameter DATA_WIDTH = 32,
    parameter DEPTH      = 1024,
    // derive address width from depth
    parameter ADDR_WIDTH = $clog2(DEPTH)
)(
    input  wire                     clk,
    input  wire                     rst,       // active-high synchronous reset

    // write interface
    input  wire                     wr_en,     // write enable
    input  wire [DATA_WIDTH-1:0]    wr_data,   // data in

    // read interface
    input  wire                     rd_en,     // read enable
    output reg  [DATA_WIDTH-1:0]    rd_data,   // data out

    // status
    output wire                     full,
    output wire                     empty,
    output reg  [ADDR_WIDTH:0]      count      // how many words currently stored
);

    // ----------------------------------------------------------------
    // Memory array
    // ----------------------------------------------------------------
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // Read / write pointers
    reg [ADDR_WIDTH-1:0] wr_ptr;
    reg [ADDR_WIDTH-1:0] rd_ptr;

    // ----------------------------------------------------------------
    // Full / Empty logic
    // ----------------------------------------------------------------
    assign empty = (count == 0);
    assign full  = (count == DEPTH);

    // ----------------------------------------------------------------
    // Write logic
    // ----------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            wr_ptr <= {ADDR_WIDTH{1'b0}};
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= wr_data;
                // increment write pointer with wrap
                if (wr_ptr == DEPTH-1)
                    wr_ptr <= {ADDR_WIDTH{1'b0}};
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end
        end
    end

    // ----------------------------------------------------------------
    // Read logic
    // ----------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            rd_ptr  <= {ADDR_WIDTH{1'b0}};
            rd_data <= {DATA_WIDTH{1'b0}};
        end else begin
            if (rd_en && !empty) begin
                rd_data <= mem[rd_ptr];
                // increment read pointer with wrap
                if (rd_ptr == DEPTH-1)
                    rd_ptr <= {ADDR_WIDTH{1'b0}};
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end
        end
    end

    // ----------------------------------------------------------------
    // Count logic
    // ----------------------------------------------------------------
    // count goes up on valid write (no read), down on valid read (no write),
    // unchanged on both or neither
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            count <= {(ADDR_WIDTH+1){1'b0}};
        end else begin
            case ({(wr_en && !full), (rd_en && !empty)})
                2'b10: count <= count + 1'b1; // write only
                2'b01: count <= count - 1'b1; // read only
                default: count <= count;      // same size
            endcase
        end
    end

endmodule
