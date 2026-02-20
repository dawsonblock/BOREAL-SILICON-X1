`default_nettype wire

module formal_test(
    input wire clk,
    input wire rst_n,
    
    // AXI Bus Inputs driven by solver
    input wire [31:0] s_axi_awaddr,
    input wire        s_axi_awvalid,
    input wire [31:0] s_axi_wdata,
    input wire [3:0]  s_axi_wstrb,
    input wire        s_axi_wvalid,
    input wire        s_axi_bready,
    input wire [31:0] s_axi_araddr,
    input wire        s_axi_arvalid,
    input wire        s_axi_rready,

    input wire [7:0]  fw_act,
    input wire [15:0] fw_val,
    
    // Outputs
    output wire        s_axi_awready,
    output wire        s_axi_wready,
    output wire [1:0]  s_axi_bresp,
    output wire        s_axi_bvalid,
    output wire        s_axi_arready,
    output wire [31:0] s_axi_rdata,
    output wire [1:0]  s_axi_rresp,
    output wire        s_axi_rvalid,
    output wire [7:0]  hw_act,
    output wire [15:0] hw_val
);

    boreal_watchdog #(
        .CLK_FREQ(10_000), // Scale down clock frequency for bounding
        .TIMEOUT_MS(1)     // 10 cycles max
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .s_axi_awaddr(s_axi_awaddr),
        .s_axi_awvalid(s_axi_awvalid),
        .s_axi_awready(s_axi_awready),
        .s_axi_wdata(s_axi_wdata),
        .s_axi_wstrb(s_axi_wstrb),
        .s_axi_wvalid(s_axi_wvalid),
        .s_axi_wready(s_axi_wready),
        .s_axi_bresp(s_axi_bresp),
        .s_axi_bvalid(s_axi_bvalid),
        .s_axi_bready(s_axi_bready),
        .s_axi_araddr(s_axi_araddr),
        .s_axi_arvalid(s_axi_arvalid),
        .s_axi_arready(s_axi_arready),
        .s_axi_rdata(s_axi_rdata),
        .s_axi_rresp(s_axi_rresp),
        .s_axi_rvalid(s_axi_rvalid),
        .s_axi_rready(s_axi_rready),
        .fw_act(fw_act),
        .fw_val(fw_val),
        .hw_act(hw_act),
        .hw_val(hw_val),
        .dbg_timer(dbg_timer),
        .dbg_safe_state(dbg_safe_state)
    );

    wire [31:0] dbg_timer;
    wire        dbg_safe_state;
    localparam MAX_CYCLES = 10;

    // Structural Assumptions
    reg f_past_valid = 0;
    always @(posedge clk) f_past_valid <= 1;

    reg init = 1;
    always @(posedge clk) init <= 0;
    always @(*) assume(rst_n == !init);

    always @(posedge clk) if (f_past_valid) begin
        assume(fw_act == $past(fw_act));
        assume(fw_val == $past(fw_val));
    end

    // Identify petting action over AXI Phase
    wire is_petting = s_axi_awvalid && s_axi_wvalid && s_axi_awready && s_axi_wready && 
                      (s_axi_awaddr[7:0] == 8'h04) && (s_axi_wdata == 32'h1CEB00DA);

    wire is_force_safe = s_axi_awvalid && s_axi_wvalid && s_axi_awready && s_axi_wready && 
                         (s_axi_awaddr[7:0] == 8'h08) && s_axi_wdata[0];

    // Property 1: Safe state engagement overrides outputs to brake
    always @(posedge clk) if (dbg_safe_state) begin
        assert(hw_act == 8'd1);
        assert(hw_val == 16'd1);
    end

    // Property 2: Non-safe state passes through standard logic
    always @(posedge clk) if (!dbg_safe_state) begin
        assert(hw_act == fw_act);
        assert(hw_val == fw_val);
    end

    // Property 3: Timer increments strictly when not petting and not forcing safe
    // Property 3: Timer increments strictly when not petting and not forcing safe
    always @(posedge clk) if (f_past_valid && $past(rst_n) && !$past(is_petting) && !$past(is_force_safe) && !$past(dbg_safe_state) && $past(dbg_timer) < MAX_CYCLES) begin
        assert(dbg_timer == $past(dbg_timer) + 1);
    end

    // Property 4: Petting resets the timer
    always @(posedge clk) if (f_past_valid && $past(rst_n) && $past(is_petting)) begin
        assert(dbg_timer == 0);
    end

    // Property 5: Bounded Liveness proof showing safe state acts after timeout
    always @(posedge clk) if (f_past_valid && $past(rst_n) && $past(dbg_timer) == MAX_CYCLES && !$past(is_petting)) begin
        assert(dbg_safe_state);
    end

endmodule
