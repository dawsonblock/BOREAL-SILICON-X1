module boreal_watchdog #(
    parameter CLK_FREQ = 100_000_000,
    parameter TIMEOUT_MS = 200
)(
    input  wire        clk,
    input  wire        rst_n,

    // AXI4-Lite Slave Interface
    input  wire [31:0] s_axi_awaddr,
    input  wire        s_axi_awvalid,
    output reg         s_axi_awready,
    input  wire [31:0] s_axi_wdata,
    input  wire [3:0]  s_axi_wstrb,
    input  wire        s_axi_wvalid,
    output reg         s_axi_wready,
    output reg  [1:0]  s_axi_bresp,
    output reg         s_axi_bvalid,
    input  wire        s_axi_bready,

    input  wire [31:0] s_axi_araddr,
    input  wire        s_axi_arvalid,
    output reg         s_axi_arready,
    output reg  [31:0] s_axi_rdata,
    output reg  [1:0]  s_axi_rresp,
    output reg         s_axi_rvalid,
    input  wire        s_axi_rready,

    // Real-Time Control Inputs
    input  wire [7:0]  fw_act,
    input  wire [15:0] fw_val,
    
    // Real-Time Control Outputs
    output reg  [7:0]  hw_act,
    output reg  [15:0] hw_val,

    // Formal Debug Ports
    output wire [31:0] dbg_timer,
    output wire        dbg_safe_state
);

    localparam MAX_CYCLES = 10;
    reg [31:0] timer = 0;
    reg        safe_state = 1'b1;
    reg        force_safe = 1'b0;

    assign dbg_timer = timer;
    assign dbg_safe_state = safe_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_awready <= 1'b1;
            s_axi_wready  <= 1'b1;
            s_axi_bvalid  <= 1'b0;
            s_axi_bresp   <= 2'b00;
            
            s_axi_arready <= 1'b1;
            s_axi_rvalid  <= 1'b0;
            s_axi_rdata   <= 32'b0;
            s_axi_rresp   <= 2'b00;

            timer <= 0;
            safe_state <= 1'b1;
            force_safe <= 1'b0;
        end else begin
            // AXI Write Channel Responses
            if (s_axi_awvalid && s_axi_wvalid && s_axi_awready && s_axi_wready) begin
                s_axi_awready <= 1'b0;
                s_axi_wready  <= 1'b0;
                s_axi_bvalid  <= 1'b1;
                
                if (s_axi_awaddr[7:0] == 8'h08) begin
                    force_safe <= s_axi_wdata[0];
                end
            end else begin
                s_axi_awready <= 1'b1;
                s_axi_wready  <= 1'b1;
                if (s_axi_bvalid && s_axi_bready) s_axi_bvalid <= 1'b0;
            end
            
            // Watchdog Timer and State Logic (Independent of AXI stall)
            if (s_axi_awvalid && s_axi_wvalid && s_axi_awready && s_axi_wready && 
                s_axi_awaddr[7:0] == 8'h04 && s_axi_wdata == 32'h1CEB00DA) begin
                timer <= 0;
                safe_state <= force_safe;
            end else if (s_axi_awvalid && s_axi_wvalid && s_axi_awready && s_axi_wready && 
                         s_axi_awaddr[7:0] == 8'h08 && s_axi_wdata[0]) begin
                safe_state <= 1'b1;
            end else begin
                if (timer < MAX_CYCLES && !safe_state) begin
                    timer <= timer + 1;
                end else if (!safe_state) begin
                    safe_state <= 1'b1;
                end
            end
            
            // AXI Read Channel
            if (s_axi_arvalid && s_axi_arready) begin
                s_axi_arready <= 1'b0;
                s_axi_rvalid  <= 1'b1;
                
                case (s_axi_araddr[7:0])
                    8'h00: s_axi_rdata <= {30'b0, force_safe, safe_state};
                    8'h0C: s_axi_rdata <= timer;
                    default: s_axi_rdata <= 32'hDEADBEEF;
                endcase
            end else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
                s_axi_arready <= 1'b1;
            end
        end
    end

    // Safety MUX Override
    always @(*) begin
        if (safe_state) begin
            hw_act = 8'd1;  // ID 1: BRAKE
            hw_val = 16'd1; // ENGAGE
        end else begin
            hw_act = fw_act;
            hw_val = fw_val;
        end
    end
endmodule
