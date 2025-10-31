module TOP_tst(

    );
    
reg clk;
reg rst;

reg task_mode;

reg         adc_mode;
reg [31:0]  adc_twake;
reg [31:0]  adc_tsam;
reg [31:0]  adc_nsam;

reg [1:0]   dac_mode;
reg [31:0]  dac_t1;
reg [31:0]  dac_t2;
reg [31:0]  dac_ts1;
reg [31:0]  dac_ts2;
reg [31:0]  dac_nsam;

reg trigger_config;
reg trigger_task;

wire done_spi;
wire done_task;

reg adc_out_rd;
reg spi_out_rd;
reg spi_wav_wr;
reg spi_config_wr;

wire [31:0] spi_out_msb;
wire [31:0] spi_out_lsb;
wire [31:0] adc_out;

reg [31:0] spi_config_msb;
reg [31:0] spi_config_lsb;
reg [31:0] spi_wav;

reg [31:0] mem_spi_config_msb [0:1];
reg [31:0] mem_spi_config_lsb [0:1];
reg [31:0] mem_spi_wav [0:255];

integer i;

WETOP Control(
    .clk(clk),
    .rst(rst),
    .task_mode(task_mode),
    .dac_mode(dac_mode),
    .dac_T1(dac_t1),
    .dac_T2(dac_t2),
    .dac_TS1(dac_ts1),
    .dac_TS2(dac_ts2),
    .dac_NSAM(dac_nsam),
    .adc_mode(adc_mode),
    .adc_TWAKE(adc_twake),
    .adc_TSAMPLE(adc_tsam),
    .adc_NSAM(adc_nsam),
    
    .trigger_config(trigger_config),
    .trigger_task(trigger_task),
    
    .done_spi(done_spi),
    .done_task(done_task),
    
    .adc_out_rd(adc_out_rd),
    .spi_out_rd(spi_out_rd),
    .spi_wav_wr(spi_wav_wr),
    .spi_config_wr(spi_config_wr),
    
    .spi_config_msb_in(spi_config_msb),
    .spi_config_lsb_in(spi_config_lsb),
    .spi_wav_in(spi_wav),
    
    .data_out_spi_msb(spi_out_msb),
    .data_out_spi_lsb(spi_out_lsb),
    .data_out_adc(adc_out),
    
    .MISO(miso),
    .MOSI(mosi),
    .CS_B(cs_b),
    .SPI_SEL(spi_sel),
    .DACSYNC(dacsync),
    .RST_ADC(rst_adc),
    .DAC_STP_EXT(dac_stp_ext),
    .SLP(slp),
    .ADC_OUT(chip_adc_out),
    .CLK_S_D_OUT(clk_s_d_out)
);

dummySPI chipspi(
    .clk(clk),
    .rst(rst),
    .spi_sel(spi_sel),
    .cs_b(cs_b),
    .mosi(mosi),
    .clk_out(spi_clk_out),
    .miso(miso)
);

dummyADC chipadc(
    .clk(clk),
    .rst_adc(rst_adc),
    .slp(slp),
    .clk_s_d_out(clk_s_d_out),
    .dout(chip_adc_out)
);

always #5 clk=~clk;

initial begin

clk = 0;
rst = 1;
task_mode = 0;

adc_mode    = 32'd1;
adc_twake   = 32'd10;
adc_tsam    = 32'd16;
adc_nsam    = 32'd2;

dac_mode    = 2'b11;
dac_t1      = 2000;
dac_t2      = 1000;
dac_ts1     = 1500; 
dac_ts2     = 750;
dac_nsam    = 8;

trigger_config = 0;
trigger_task = 0;

adc_out_rd = 0;
spi_out_rd = 0;
spi_config_wr = 0;
spi_wav_wr = 0;

spi_wav = 0;
spi_config_msb = 0;
spi_config_lsb = 0;

$readmemb("mem_wav.mem",mem_spi_wav);
$readmemb("mem_config_msb.mem",mem_spi_config_msb);
$readmemb("mem_config_lsb.mem",mem_spi_config_lsb);

#10 rst = 0;



for (i=0; i<2; i=i+1) begin
    #10
    spi_config_msb = mem_spi_config_msb[i];
    spi_config_lsb = mem_spi_config_lsb[i];
    #10
    spi_config_wr = 1;
    #10
    spi_config_wr = 0;
end

for (i=0; i<8; i=i+1) begin
    #10
    spi_wav = mem_spi_wav[i];
    #10
    spi_wav_wr = 1;
    #10
    spi_wav_wr = 0;
end

#10
trigger_config = 1;
#10
trigger_config = 0;
#1000
trigger_config = 1;
#10
trigger_config = 0;
#1000


spi_out_rd = 1;
#20
spi_out_rd = 0;
#100

trigger_task = 1;
#10
trigger_task = 0;

@(posedge done_task);
#100
adc_out_rd = 1;
#100
adc_out_rd = 0;

//#10000;

$finish;
end

endmodule
