#include "StoryItem.h"
#include "Endless.h"
#include "LoopManager.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

AStoryItem::AStoryItem()
{
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	Mesh->SetStaticMesh(Cube.Object);
	Mesh->SetRelativeScale3D(FVector(0.2f));
}

void AStoryItem::BeginPlay()
{
	Super::BeginPlay();

	TActorIterator<ALoopManager> It(GetWorld());
	Manager = It ? *It : nullptr;
	if (!Manager)
	{
		UE_LOG(LogEndless, Error, TEXT("%s: no LoopManager in level"), *GetActorNameOrLabel());
	}
}

void AStoryItem::Interact_Implementation(AActor* Caller)
{
	if (!Manager)
	{
		return;
	}
	Manager->CompleteObjective();
	UE_LOG(LogEndless, Log, TEXT("%s used: stage %d objective done"), *GetActorNameOrLabel(), Manager->CurrentStage);
	if (bHideOnUse)
	{
		SetActorHiddenInGame(true);
		SetActorEnableCollision(false);
	}
	OnUsed();
}
