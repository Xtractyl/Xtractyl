import React from "react";
import dinoGif from "../assets/xtractyl_loader.gif"; 

export default function DinoLoader() {
  return (
    <img
      src={dinoGif}
      alt="Loading Dino"
      className="w-32 h-auto mx-auto animate-pulse"
    />
  );
}