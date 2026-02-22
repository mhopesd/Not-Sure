import imgCanvas from "figma:asset/ca5fce22546b59935a52e79b90d0ac65f0d6b592.png";
import imgCanvas1 from "figma:asset/a8e26a9c615d4f5c5ae2c03afd90d74b0571babe.png";
import imgCanvas2 from "figma:asset/55daa013c0552bf445783f854fbf7fc447565b7c.png";
import imgCanvas3 from "figma:asset/acb1bc3f471463798dc2f515577069108a9dc771.png";
import imgCanvas4 from "figma:asset/4f76cca71a9739963b087e6ccf456bedc935d31f.png";

function Section() {
  return <div className="absolute left-[585.5px] size-0 top-[129.15px]" data-name="Section" />;
}

function Canvas() {
  return (
    <div className="relative rounded-[16777200px] shrink-0 size-[603px]" data-name="Canvas">
      <img alt="" className="absolute bg-clip-padding border-0 border-[transparent] border-solid inset-0 max-w-none object-contain pointer-events-none rounded-[16777200px] size-full" src={imgCanvas} />
    </div>
  );
}

function Container() {
  return (
    <div className="absolute content-stretch flex flex-col items-center justify-center left-[284.15px] size-[602.695px] top-[129.15px]" data-name="Container">
      <Canvas />
    </div>
  );
}

function T() {
  return (
    <div className="absolute bg-black h-[861px] left-0 top-0 w-[1171px]" data-name="T0">
      <Section />
      <Container />
    </div>
  );
}

function Canvas1() {
  return (
    <div className="absolute left-0 rounded-[16777200px] size-[31px] top-0" data-name="Canvas">
      <img alt="" className="absolute inset-0 max-w-none object-contain pointer-events-none rounded-[16777200px] size-full" src={imgCanvas1} />
    </div>
  );
}

function Button() {
  return (
    <div className="absolute bg-[rgba(255,255,255,0)] border-2 border-[rgba(255,255,255,0.3)] border-solid left-0 overflow-clip rounded-[16777200px] size-[35px] top-0" data-name="Button">
      <Canvas1 />
    </div>
  );
}

function Canvas2() {
  return (
    <div className="absolute left-0 rounded-[16777200px] size-[34.1px] top-0" data-name="Canvas">
      <img alt="" className="absolute inset-0 max-w-none object-contain pointer-events-none rounded-[16777200px] size-full" src={imgCanvas2} />
    </div>
  );
}

function Button1() {
  return (
    <div className="absolute bg-[rgba(255,255,255,0)] border-2 border-solid border-white left-[-1.75px] overflow-clip rounded-[16777200px] shadow-[0px_0px_10px_0px_rgba(255,255,255,0.5)] size-[38.5px] top-[47.25px]" data-name="Button">
      <Canvas2 />
    </div>
  );
}

function Canvas3() {
  return (
    <div className="absolute left-0 rounded-[16777200px] size-[31px] top-0" data-name="Canvas">
      <img alt="" className="absolute inset-0 max-w-none object-contain pointer-events-none rounded-[16777200px] size-full" src={imgCanvas3} />
    </div>
  );
}

function Button2() {
  return (
    <div className="absolute bg-[rgba(255,255,255,0)] border-2 border-[rgba(255,255,255,0.3)] border-solid left-0 overflow-clip rounded-[16777200px] size-[35px] top-[98px]" data-name="Button">
      <Canvas3 />
    </div>
  );
}

function Canvas4() {
  return (
    <div className="absolute left-0 rounded-[16777200px] size-[31px] top-0" data-name="Canvas">
      <img alt="" className="absolute inset-0 max-w-none object-contain pointer-events-none rounded-[16777200px] size-full" src={imgCanvas4} />
    </div>
  );
}

function Button3() {
  return (
    <div className="absolute bg-[rgba(255,255,255,0)] border-2 border-[rgba(255,255,255,0.3)] border-solid left-0 overflow-clip rounded-[16777200px] size-[35px] top-[147px]" data-name="Button">
      <Canvas4 />
    </div>
  );
}

function Container1() {
  return (
    <div className="absolute h-[185.5px] left-[1122px] top-[337.75px] w-[35px]" data-name="Container">
      <Button />
      <Button1 />
      <Button2 />
      <Button3 />
    </div>
  );
}

export default function ShaderReminderCommunity() {
  return (
    <div className="bg-white relative size-full" data-name="Shader Reminder (Community)">
      <T />
      <Container1 />
    </div>
  );
}