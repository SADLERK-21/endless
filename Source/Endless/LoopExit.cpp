#include "LoopExit.h"
#include "Endless.h"
#include "LoopManager.h"
#include "EngineUtils.h"
#include "Components/ArrowComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"

ALoopExit::ALoopExit()
{
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	Box = CreateDefaultSubobject<UBoxComponent>(TEXT("Box"));
	Box->SetupAttachment(RootComponent);
	Box->InitBoxExtent(FVector(10.f, 100.f, 120.f));
	Box->SetRelativeLocation(FVector(0.f, 0.f, 120.f)); // bottom of the box on the pivot = on the floor
	Box->SetCollisionProfileName(TEXT("Trigger"));

	Arrow = CreateDefaultSubobject<UArrowComponent>(TEXT("Arrow"));
	Arrow->SetupAttachment(RootComponent);
	Arrow->ArrowSize = 2.f;
}

void ALoopExit::BeginPlay()
{
	Super::BeginPlay();

	if (!Manager)
	{
		TActorIterator<ALoopManager> It(GetWorld());
		Manager = It ? *It : nullptr;
	}
	if (!Manager)
	{
		UE_LOG(LogEndless, Error, TEXT("%s: no LoopManager in level"), *GetActorNameOrLabel());
		return;
	}
	Box->OnComponentBeginOverlap.AddDynamic(this, &ALoopExit::OnBeginOverlap);
}

void ALoopExit::OnBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp,
	int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	APawn* Pawn = Cast<APawn>(OtherActor);
	if (Pawn && Pawn->IsPlayerControlled())
	{
		Manager->HandleExit(this, Pawn);
	}
}
