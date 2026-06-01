const canvas =
    document.getElementById(
        "gameCanvas"
    );

const ctx =
    canvas.getContext("2d");

let ballX = 400;
let ballY = 400;

function draw()
{
    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    ctx.beginPath();

    ctx.arc(
        ballX,
        ballY,
        10,
        0,
        Math.PI * 2
    );

    ctx.fill();

    requestAnimationFrame(
        draw
    );
}

draw();

const ws =
    new WebSocket(
        "ws://127.0.0.1:8000/host"
    );

    ws.onmessage = (event) =>
{
    const data =
        JSON.parse(
            event.data
        );

    if(
        data.type ===
        "game_state"
    )
    {
        ballX =
            data.ball_x;

        ballY =
            data.ball_y;
    }
};