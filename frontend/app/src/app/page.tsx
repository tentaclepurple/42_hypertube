import Image from "next/image";

export default function Home() {

  const images = [
    "/hypertube42.png",
    "/hypertube.png",
    "/hyperheros.png",
  ];

  const randomImage = images[Math.floor(Math.random() * images.length)];
  return (
    <main className="flex flex-col items-center justify-between p-4 sm:p-10">
      <h1 className="text-2xl sm:text-4xl font-bold text-center">Welcome to Hypertube</h1>
      <div className="w-full max-w-md sm:max-w-lg">
        <Image 
          src={randomImage}
          alt="Home Image"
          width={0}
          height={0}
          className="mt-4 sm:mt-6 rounded-lg"
          style={{ width: "100%", height: "auto" }}
          sizes="(max-width: 768px) 100vw, 50vw"
        />
      </div>
      <p className="mt-2 sm:mt-4 text-base sm:text-lg text-center">Dive into the ultimate movie universe</p>
    </main>
  )
}
